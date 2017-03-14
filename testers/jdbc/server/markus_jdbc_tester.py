#!/usr/bin/env python3

import os
import subprocess

from markus_utils import MarkusUtilsMixin
from markus_sql_tester import MarkusSQLTester


class MarkusJDBCTester(MarkusSQLTester):

    ERROR_MSGS = {
        'bad_javac': "Java compilation error: '{}'",
        'bad_java': "Java runtime error: 'stdout: {}', 'stderr: {}'",
        'skip_sql': 'Java test failure, not checking SQL'
    }
    ERROR_MSGS.update(MarkusSQLTester.ERROR_MSGS)
    CONNECTION_TEST = 'Connection Test'

    def __init__(self, oracle_database, test_database, user_name, user_password, path_to_solution, schema_name,
                 java_specs, java_files, java_jar, sql_specs, output_filename='feedback_jdbc.txt'):
        super().__init__(oracle_database, test_database, user_name, user_password, path_to_solution, schema_name,
                         java_specs, {}, output_filename)
        self.java_files = java_files
        self.java_classpath = '.:{}:{}'.format(path_to_solution, java_jar)
        self.sql_specs = sql_specs

    def init_java(self):
        javac_command = ['javac', '-cp', self.java_classpath, '{}.java'.format(self.__class__.__name__)]
        subprocess.run(javac_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                       check=True)

    def check_java(self, test_name, data_file, points_total):
        if data_file is None:
            data_file = 'nodata.sql'
        java_command = ['java', '-cp', self.java_classpath, self.__class__.__name__, self.oracle_database,
                        self.test_database, self.user_name, self.user_password, test_name, data_file, str(points_total)]
        java = subprocess.run(java_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                              check=True)

        return java.stderr, java.stdout

    def get_test_results(self, table_name, sql_file, sql_order_file=None):
        query, query_vars = self.select_query(schema_name=self.schema_name, table_name=table_name)
        self.test_cursor.execute(query, query_vars)
        self.test_connection.commit()
        test_results = self.test_cursor.fetchall()

        return test_results

    def run(self):

        try:
            for java_file in self.java_files:
                # check that the submission exists
                if not os.path.isfile(java_file):
                    msg = self.ERROR_MSGS['no_submission'].format(java_file)
                    MarkusUtilsMixin.print_test_error(name='All JDBC tests', message=msg)
                    return
            try:
                # compile the java files
                self.init_java()
            except subprocess.CalledProcessError as e:
                msg = self.ERROR_MSGS['bad_javac'].format(e.stdout)
                MarkusUtilsMixin.print_test_error(name='All JDBC tests', message=msg)
                return
            self.init_db()
            with open(self.output_filename, 'w') as output_open:
                for test_name in sorted(self.specs.keys()):
                    for data_file, java_points_total in sorted(self.specs[test_name].items()):
                        if data_file is None:  # connection test
                            data_name = None
                            test_data_name = test_name
                        else:
                            data_name = os.path.splitext(data_file)[0]
                            test_data_name = '{} + {}'.format(test_name, data_name)
                        # JAVA: drop and recreate test schema + dataset, then run java
                        java_fail = False
                        java_test_data_name = 'JAVA {}'.format(test_data_name)
                        try:
                            self.set_test_schema(data_file=data_file)
                            test_output, file_output = self.check_java(test_name=test_name, data_file=data_file,
                                                                       points_total=java_points_total)
                            print(test_output)
                            output_open.write(file_output)
                            if '<status>pass</status>' not in test_output:
                                java_fail = True  # don't run SQL
                        except Exception as e:
                            self.oracle_connection.commit()
                            self.test_connection.commit()
                            msg = self.ERROR_MSGS['bad_java'].format(e.stdout, e.stderr)\
                                if isinstance(e, subprocess.CalledProcessError) else str(e)
                            MarkusUtilsMixin.print_test_error(name=java_test_data_name, message=msg,
                                                              points_total=java_points_total)
                            self.print_file_error(output_open=output_open, name=java_test_data_name, feedback=msg)
                            java_fail = True  # don't run SQL
                        if test_name not in self.sql_specs:
                            continue
                        # SQL: fetch and compare sql results
                        for table_name, sql_points_total in self.sql_specs[test_name][data_file]:
                            sql_test_data_name = 'SQL({}) {}'.format(table_name, test_data_name)
                            try:
                                if java_fail:
                                    raise Exception(self.ERROR_MSGS['skip_sql'])
                                test_results = self.get_test_results(table_name=table_name, sql_file=None)
                                oracle_results = self.get_oracle_results(schema_name=data_name, table_name=table_name)
                                output, status = self.check_results(oracle_results=oracle_results,
                                                                    test_results=test_results, order_on=False)
                                points_awarded = sql_points_total if status == 'pass' else 0
                                MarkusUtilsMixin.print_test_result(name=sql_test_data_name, status=status,
                                                                   output=output, points_awarded=points_awarded,
                                                                   points_total=sql_points_total)
                                self.print_file_psql(output_open=output_open, name=sql_test_data_name,
                                                     oracle_schema_name=data_name, table_name=table_name, status=status,
                                                     feedback=output)
                            except Exception as e:
                                self.oracle_connection.commit()
                                self.test_connection.commit()
                                MarkusUtilsMixin.print_test_error(name=sql_test_data_name, message=str(e),
                                                                  points_total=sql_points_total)
                                self.print_file_error(output_open=output_open, name=sql_test_data_name, feedback=str(e))
        except Exception as e:
            MarkusUtilsMixin.print_test_error(name='All JDBC tests', message=str(e))
        finally:
            self.close_db()
