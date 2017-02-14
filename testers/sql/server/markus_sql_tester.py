import os
import pprint
import subprocess

import psycopg2
from markus_utils import MarkusUtilsMixin
# from markusapi import Markus


class MarkusSQLTester(MarkusUtilsMixin):

    SCHEMA_FILE = 'schema.ddl'
    DATASET_DIR = 'datasets'
    QUERY_DIR = 'queries'

    def __init__(self, oracle_database, test_database, user_name, user_password, path_to_solution, schema_name, specs,
                 order_bys={}, output_filename='result.txt'):
        self.oracle_database = oracle_database
        self.test_database = test_database
        self.user_name = user_name
        self.user_password = user_password
        self.path_to_solution = path_to_solution
        self.schema_name = schema_name
        self.specs = specs
        self.order_bys = order_bys
        self.output_filename = output_filename
        self.oracle_connection = None
        self.oracle_cursor = None
        self.test_connection = None
        self.test_cursor = None

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

    def get_oracle_results(self, data_name, test_name):
        self.oracle_cursor.execute('SELECT * FROM %(schema)s.%(table)s',
                                   {'schema': psycopg2.extensions.AsIs(data_name.lower()),
                                    'table': psycopg2.extensions.AsIs('oracle_{}'.format(test_name.lower()))})
        self.oracle_connection.commit()
        oracle_results = self.oracle_cursor.fetchall()

        return oracle_results

    def set_test_schema(self, data_file):
        self.test_cursor.execute('DROP SCHEMA IF EXISTS %(schema)s CASCADE',
                                 {'schema': psycopg2.extensions.AsIs(self.schema_name)})
        self.test_cursor.execute('CREATE SCHEMA %(schema)s', {'schema': psycopg2.extensions.AsIs(self.schema_name)})
        self.test_cursor.execute('SET search_path TO %(schema)s',
                                 {'schema': psycopg2.extensions.AsIs(self.schema_name)})
        with open(os.path.join(self.path_to_solution, self.SCHEMA_FILE)) as schema_open:
            schema = schema_open.read()
            self.test_cursor.execute(schema)
        with open(os.path.join(self.path_to_solution, self.DATASET_DIR, data_file)) as data_open:
            data = data_open.read()
            self.test_cursor.execute(data)
        self.test_connection.commit()

    def get_test_results(self, sql_file):
        with open(sql_file) as sql_open:
            sql = sql_open.read()
            self.test_cursor.execute(sql)
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
            return 'Expected {} columns instead of {}'.format(oracle_num_columns, test_num_columns), 'fail'

        check_column_types = []
        for i, oracle_column in enumerate(oracle_columns):
            # check 2: column names + order
            if test_columns[i].name != oracle_column.name:
                return "Expected column {} to have name '{}' instead of '{}'".format(i, oracle_column.name,
                                                                                     test_columns[i].name), 'fail'
            # check 3: column types
            # (strictly different PostgreSQL oid types can be Python-compatible instead, e.g. varchar and text, so this
            # check will be deferred to row analysis)
            if test_columns[i].type_code != oracle_column.type_code:
                if not oracle_results and not test_results:
                    return "The type of values in column '{}' does not match the expected type (but no row values are "\
                           "available to check whether they could be compatible types)".format(
                            oracle_column.name), 'fail'
                if not oracle_results or not test_results:  # will fail on check 4 instead
                    continue
                check_column_types.append(i)

        # check 4: rows count
        oracle_num_results = len(oracle_results)
        test_num_results = len(test_results)
        if oracle_num_results != test_num_results:
            return 'Expected {} rows instead of {}'.format(oracle_num_results, test_num_results), 'fail'

        for i, oracle_row in enumerate(oracle_results):
            if order_on:
                test_row = test_results[i]
            else:
                # check 5, unordered variant: rows content
                try:
                    t = test_results.index(oracle_row)
                    test_row = test_results.pop(t)
                except ValueError:
                    return 'Expected to find a row {} in the unordered results'.format(oracle_row), 'fail'
            checked_column_types = []
            for j in check_column_types:
                # check 3: column type compatibility deferred trigger
                oracle_value = oracle_row[j]
                test_value = test_row[j]
                if test_value is None or oracle_value is None:  # try next row for types
                    continue
                if type(test_value) is not type(oracle_value):
                    return "The type of values in column '{}' does not match the expected type".format(
                        oracle_columns[j].name), 'fail'
                checked_column_types.append(j)
            check_column_types = [j for j in check_column_types if j not in checked_column_types]
            # check 5, ordered variant: rows content + order
            if order_on and oracle_row != test_row:
                return 'Expected row {} in the ordered results to be {} instead of {}'.format(i, oracle_row,
                                                                                              test_results[i]), 'fail'
        # check 3: column type compatibility deferred trigger
        if check_column_types:
            return "The type of values in column '{}' does not match the expected type (but no row values are "\
                   "available to check whether they could be compatible types)".format(
                    oracle_columns[check_column_types[0]].name), 'fail'

        # all good
        return '', 'pass'

    def print_summary_file(self, output_open, test_name, actual, status):
        output_open.write('========== {} - {} ==========\n'.format(test_name, status.upper()))
        if actual:
            output_open.write(' Problem: {}\n'.format(actual))

    def print_result_file(self, output_open, test_name, actual, status, oracle_results, test_results):
        self.print_summary_file(output_open, test_name, actual, status)
        output_open.write(' Expected Columns:\n  {}\n'.format(pprint.pformat([column.name for column in
                                                                              self.oracle_cursor.description])))
        output_open.write(' Actual Columns:\n  {}\n'.format(pprint.pformat([column.name for column in
                                                                            self.test_cursor.description])))
        output_open.write(' Expected Rows:\n')
        for oracle_result in oracle_results:
            output_open.write('  {}\n'.format(pprint.pformat(oracle_result)))
        output_open.write(' Actual Rows:\n')
        for test_result in test_results:
            output_open.write('  {}\n'.format(pprint.pformat(test_result)))
        output_open.write('\n')

    def print_error_file(self, output_open, test_name, actual):
        self.print_summary_file(output_open, test_name, actual, 'error')
        output_open.write('\n')

    def print_psql_file(self, output_open, data_name, test_name, status, feedback):
        output_open.write('========== {} + {}: {} ==========\n'.format(test_name, data_name, status.upper()))
        if feedback:
            output_open.write('Feedback: {}\n'.format(feedback))
        if status != 'pass':
            oracle_query = 'SELECT * FROM {}.oracle_{}'.format(data_name, test_name)
            oracle_command = ['psql', '-U', self.user_name, '-d', self.oracle_database, '-h', 'localhost', '-c',
                              oracle_query]
            test_command = ['psql', '-U', self.user_name, '-d', self.test_database, '-h', 'localhost', '-f',
                            '{}.sql'.format(test_name)]
            env = os.environ.copy()
            env['PGPASSWORD'] = self.user_password
            proc = subprocess.run(oracle_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                                  shell=False, env=env, universal_newlines=True)
            output_open.write(proc.stdout)
            proc = subprocess.run(test_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=False,
                                  env=env, universal_newlines=True)
            output_open.write(proc.stdout)
        output_open.write('\n')

    def run(self):

        # TODO
        # 1) Add order_bys as constructor parameter
        # 2) Handle separate *_order.sql files if order_by is present
        # 3) Check results by:
        #  a) checking a table named like the student file, irrespective of order
        #  b) executing the order file for students and the order_by directive for oracle
        # 4) Modify the psql dump as per 3)
        # 5) Send the feedback file back to the students by committing it to their repo
        # 99) Update all examples
        # TODO
        try:
            with open(self.output_filename, 'w') as output_open:
                self.init_db()
                for sql_file in sorted(self.specs.keys()):
                    test_name = sql_file.partition('.')[0]
                    for data_file, points_total in sorted(self.specs[sql_file].items()):
                        data_name = data_file.partition('.')[0]
                        test_data_name = '{} + {}'.format(test_name, data_name)
                        if not os.path.isfile(sql_file):
                            msg = 'File {} not found'.format(sql_file)
                            MarkusUtilsMixin.print_test_error(name=test_data_name, message=msg,
                                                              points_total=points_total)
                            self.print_error_file(output_open=output_open, test_name=test_data_name, actual=msg)
                            continue
                        try:
                            # drop + recreate test schema + dataset + fetch test results
                            self.set_test_schema(data_file=data_file)
                            test_results = self.get_test_results(sql_file=sql_file)
                            # fetch results from oracle
                            oracle_results = self.get_oracle_results(data_name=data_name, test_name=test_name)
                            # compare test results with oracle
                            output, status = self.check_results(oracle_results=oracle_results,
                                                                test_results=test_results)
                            points_awarded = points_total if status == 'pass' else 0
                            MarkusUtilsMixin.print_test_result(name=test_data_name, status=status, output=output,
                                                               points_awarded=points_awarded, points_total=points_total)
                            # self.print_result_file(output_open=output_open, test_name=test_data_name,
                            #                        actual=output, status=status, oracle_results=oracle_results,
                            #                        test_results=test_results)
                            self.print_psql_file(output_open=output_open, data_name=data_name, test_name=test_name,
                                                 status=status, feedback=output)
                        except Exception as e:
                            self.oracle_connection.commit()
                            self.test_connection.commit()
                            MarkusUtilsMixin.print_test_error(name=test_data_name, message=str(e),
                                                              points_total=points_total)
                            self.print_error_file(output_open=output_open, test_name=test_data_name, actual=str(e))
        except Exception as e:
            MarkusUtilsMixin.print_test_error(name='All SQL tests', message=str(e))
        finally:
            self.close_db()
