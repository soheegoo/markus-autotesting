import contextlib
import os
import subprocess

import psycopg2

from markus_tester import MarkusTester, MarkusTest, MarkusTestSpecs


class MarkusSQLTester(MarkusTester):

    SCHEMA_FILE = 'schema.ddl'
    DATASET_DIR = 'datasets'
    QUERY_DIR = 'queries'

    def __init__(self, specs):
        super().__init__(specs=specs)
        self.oracle_database = specs['oracle_database']
        self.test_database = specs['test_database']
        self.user_name = specs['user_name']
        self.user_password = specs['user_password']
        self.path_to_solution = specs['path_to_solution']
        self.schema_name = specs['schema_name']
        self.oracle_connection = None
        self.oracle_cursor = None
        self.test_connection = None
        self.test_cursor = None

    def create_test(self, test_file, data_files, test_data_config, test_extra, feedback_open):
        return MarkusSQLTest(test_file, data_files, test_data_config, test_extra, feedback_open)

    def init_db(self):
        self.oracle_connection = psycopg2.connect(database=self.oracle_database, user=self.user_name,
                                                  password=self.user_password, host='localhost')
        self.oracle_cursor = self.oracle_connection.cursor()
        self.test_connection = psycopg2.connect(database=self.test_database, user=self.user_name,
                                                password=self.user_password, host='localhost')
        self.test_cursor = self.test_connection.cursor()

    def close_db(self):
        if self.test_cursor:
            self.test_cursor.close()
        if self.test_connection:
            self.test_connection.close()
        if self.oracle_cursor:
            self.oracle_cursor.close()
        if self.oracle_connection:
            self.oracle_connection.close()

    def run(self):
        try:
            self.init_db()
            with contextlib.ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.specs.feedback_file, 'w'))
                                 if self.specs.feedback_file is not None
                                 else None)
                for test_file in sorted(self.specs.test_files):
                    test_extra = self.specs.matrix[test_file].get(MarkusTestSpecs.MATRIX_NONTEST_KEY)
                    for data_file in sorted(self.specs.matrix[test_file].keys()):
                        if data_file == MarkusTestSpecs.MATRIX_NONTEST_KEY:
                            continue
                        points = self.specs.matrix[test_file][data_file]
                        test = self.create_test(test_file, [data_file], points, test_extra, feedback_open)
                        xml = test.run()
                        print(xml)
        except Exception as e:
            print(MarkusTester.error_all(message=str(e)))
        finally:
            self.close_db()


class MarkusSQLTest(MarkusTest):

    ERROR_MSGS = {
        'no_submission': "Submission file '{}' not found",
        'no_submission_order': "Ordering required, order file '{}' not found",
        'bad_col_count': 'Expected {} columns instead of {}',
        'bad_col_name': "Expected column {} to have name '{}' instead of '{}'",
        'bad_col_type': "Expected a different type of values in column '{}' (expected a SQL equivalent of Python type "
                        "'{}' instead of '{}')",
        'bad_col_type_maybe': "Expected a different type of values in column '{}' (but no row values are available to "
                              "check whether they could be compatible types)",
        'bad_row_count': 'Expected {} rows instead of {}',
        'bad_row_content_no_order': 'Expected to find a row {} in the results',
        'bad_row_content_order': 'Expected row {} in the ordered results to be {} instead of {}'
    }

    def __init__(self, test_file, data_files, points, test_extra, feedback_open):
        super().__init__(test_file, data_files, points, test_extra, feedback_open)
        self.data_file = data_files[0]

    @staticmethod
    def select_query(schema_name, table_name, order_by=None):
        query = 'SELECT * FROM %(schema)s.%(table)s'
        query_vars = {'schema': psycopg2.extensions.AsIs(schema_name.lower()),
                      'table': psycopg2.extensions.AsIs(table_name.lower())}
        if order_by:
            query += ' ORDER BY %(order)s'
            query_vars['order'] = psycopg2.extensions.AsIs(order_by)

        return query, query_vars

    def get_oracle_results(self, schema_name, table_name, order_by=None):
        query, query_vars = self.select_query(schema_name=schema_name, table_name=table_name, order_by=order_by)
        self.oracle_cursor.execute(query, query_vars)
        self.oracle_connection.commit()
        oracle_results = self.oracle_cursor.fetchall()

        return oracle_results

    def set_test_schema(self, data_file=None):
        self.test_cursor.execute('DROP SCHEMA IF EXISTS %(schema)s CASCADE',
                                 {'schema': psycopg2.extensions.AsIs(self.schema_name)})
        self.test_cursor.execute('CREATE SCHEMA %(schema)s', {'schema': psycopg2.extensions.AsIs(self.schema_name)})
        self.test_cursor.execute('SET search_path TO %(schema)s',
                                 {'schema': psycopg2.extensions.AsIs(self.schema_name)})
        with open(os.path.join(self.path_to_solution, self.SCHEMA_FILE)) as schema_open:
            schema = schema_open.read()
            self.test_cursor.execute(schema)
        if data_file is not None:
            with open(os.path.join(self.path_to_solution, self.DATASET_DIR, data_file)) as data_open:
                data = data_open.read()
                self.test_cursor.execute(data)
        self.test_connection.commit()

    def get_test_results(self, table_name, sql_file, sql_order_file=None):
        with open(sql_file) as sql_open:
            sql = sql_open.read()
            self.test_cursor.execute(sql)
        if sql_order_file is not None:
            with open(sql_order_file) as sql_order_open:
                sql = sql_order_open.read()
                self.test_cursor.execute(sql)
        else:
            query, query_vars = self.select_query(schema_name=self.schema_name, table_name=table_name)
            self.test_cursor.execute(query, query_vars)
        self.test_connection.commit()
        test_results = self.test_cursor.fetchall()

        return test_results

    def check_results(self, oracle_results, test_results, order_on=True):

        oracle_columns = self.oracle_cursor.description
        test_columns = self.test_cursor.description

        # check 1: column count
        oracle_num_columns = len(oracle_columns)
        test_num_columns = len(test_columns)
        if oracle_num_columns != test_num_columns:
            return self.ERROR_MSGS['bad_col_count'].format(oracle_num_columns, test_num_columns), 'fail'

        check_column_types = []
        for i, oracle_column in enumerate(oracle_columns):
            # check 2: column names + order
            if test_columns[i].name != oracle_column.name:
                return self.ERROR_MSGS['bad_col_name'].format(i, oracle_column.name, test_columns[i].name), 'fail'
            # check 3: column types
            # (strictly different PostgreSQL oid types can be Python-compatible instead, e.g. varchar and text, so this
            # check will be deferred to row analysis)
            if test_columns[i].type_code != oracle_column.type_code:
                if not oracle_results and not test_results:
                    return self.ERROR_MSGS['bad_col_type_maybe'].format(oracle_column.name), 'fail'
                if not oracle_results or not test_results:  # will fail on check 4 instead
                    continue
                check_column_types.append(i)

        # check 4: row count
        oracle_num_results = len(oracle_results)
        test_num_results = len(test_results)
        if oracle_num_results != test_num_results:
            return self.ERROR_MSGS['bad_row_count'].format(oracle_num_results, test_num_results), 'fail'

        for i, oracle_row in enumerate(oracle_results):
            if order_on:
                test_row = test_results[i]
            else:
                # check 5, unordered variant: row contents
                try:
                    t = test_results.index(oracle_row)
                    test_row = test_results.pop(t)
                except ValueError:
                    return self.ERROR_MSGS['bad_row_content_no_order'].format(oracle_row), 'fail'
            checked_column_types = []
            for j in check_column_types:
                # check 3: column types compatibility deferred trigger
                oracle_value = oracle_row[j]
                test_value = test_row[j]
                if test_value is None or oracle_value is None:  # try next row for types
                    continue
                oracle_type = type(oracle_value)
                test_type = type(test_value)
                if test_type is not oracle_type:
                    return self.ERROR_MSGS['bad_col_type'].format(oracle_columns[j].name, oracle_type.__name__,
                                                                  test_type.__name__), 'fail'
                checked_column_types.append(j)
            check_column_types = [j for j in check_column_types if j not in checked_column_types]
            # check 5, ordered variant: row contents + order
            if order_on and oracle_row != test_row:
                return self.ERROR_MSGS['bad_row_content_order'].format(i, oracle_row, test_results[i]), 'fail'
        # check 3: column types compatibility deferred trigger
        if check_column_types:
            return self.ERROR_MSGS['bad_col_type_maybe'].format(oracle_columns[check_column_types[0]].name), 'fail'

        # all good
        return '', 'pass'

    @staticmethod
    def print_file_summary(output_open, name, status, feedback):
        # test summary
        output_open.write('========== {}: {} ==========\n\n'.format(name, status.upper()))
        # feedback
        if feedback:
            output_open.write('## Feedback: {}\n\n'.format(feedback))

    # TODO Refactor as add_feedback
    def print_file_psql(self, output_open, name, oracle_schema_name, table_name, status, feedback, order_by=None,
                        sql_order_file=None):
        # header
        self.print_file_summary(output_open=output_open, name=name, status=status, feedback=feedback)
        # table dump using psql if not passed
        if status != 'pass':
            oracle_query, oracle_vars = self.select_query(schema_name=oracle_schema_name, table_name=table_name,
                                                          order_by=order_by)
            oracle_command = ['psql', '-U', self.user_name, '-d', self.oracle_database, '-h', 'localhost', '-c',
                              self.oracle_cursor.mogrify(oracle_query, oracle_vars)]
            test_command = ['psql', '-U', self.user_name, '-d', self.test_database, '-h', 'localhost']
            if sql_order_file is not None:
                test_command.extend(['-f', sql_order_file])
            else:
                test_query, test_vars = self.select_query(schema_name=self.schema_name, table_name=table_name)
                test_command.extend(['-c', self.test_cursor.mogrify(test_query, test_vars)])
            # comparison of solutions
            env = os.environ.copy()
            env['PGPASSWORD'] = self.user_password
            output_open.write('## Expected Solution:\n\n')
            proc = subprocess.run(oracle_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                                  shell=False, env=env, universal_newlines=True)
            output_open.write(proc.stdout)
            output_open.write('## Your Solution:\n\n')
            proc = subprocess.run(test_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=False,
                                  env=env, universal_newlines=True)
            output_open.write(proc.stdout)
        output_open.write('\n')

    def print_file_error(self, output_open, name, feedback):
        self.print_file_summary(output_open=output_open, name=name, status='error', feedback=feedback)
        output_open.write('\n')

    def run(self):

        # check that the submission exists
        if not os.path.isfile(self.test_file):
            msg = self.ERROR_MSGS['no_submission'].format(self.test_file)
            self.print_file_error(output_open=self.feedback_open, name=self.test_data_name, feedback=msg)
            return self.error(message=msg)
        # check if ordering is required
        sql_order_file = None
        order_by = self.order_bys.get(self.test_file)
        if order_by:
            sql_order_file = '{}_order{}'.format(self.test_name, os.path.splitext(self.test_file)[1])
            if not os.path.isfile(sql_order_file):
                msg = self.ERROR_MSGS['no_submission_order'].format(sql_order_file)
                self.print_file_error(output_open=self.feedback_open, name=self.test_data_name, feedback=msg)
                return self.error(message=msg)
        try:
            # drop and recreate test schema + dataset, then fetch and compare results
            self.set_test_schema(data_file=self.data_file)
            test_results = self.get_test_results(table_name=self.test_name, sql_file=self.test_file,
                                                 sql_order_file=sql_order_file)
            oracle_results = self.get_oracle_results(schema_name=self.data_name, table_name=self.test_name,
                                                     order_by=order_by)
            order_on = True if order_by else False
            output, status = self.check_results(oracle_results=oracle_results, test_results=test_results,
                                                order_on=order_on)
            self.print_file_psql(output_open=self.feedback_open, name=self.test_data_name,
                                 oracle_schema_name=self.data_name, table_name=self.test_name, status=status,
                                 feedback=output, order_by=order_by, sql_order_file=sql_order_file)
            if status == 'pass':
                return self.passed()
            else:
                return self.failed(points_awarded=0, message=output)
        except Exception as e:
            self.oracle_connection.commit()
            self.test_connection.commit()
            self.print_file_error(output_open=self.feedback_open, name=self.test_data_name, feedback=str(e))
            return self.error(message=str(e))
