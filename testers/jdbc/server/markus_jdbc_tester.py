import os
import subprocess

from markus_sql_tester import MarkusSQLTester, MarkusSQLTest
from markus_tester import MarkusTester


class MarkusJDBCTest(MarkusSQLTest):

    ERROR_MSGS = {
        'bad_javac': "Java compilation error: '{}'",
        'bad_java': "Java runtime error: '{}'",
        'skip_sql': 'Java test failure, will not check SQL'
    }
    ERROR_MSGS.update(MarkusSQLTest.ERROR_MSGS)

    def __init__(self, tester, test_file, data_files, points, test_extra, feedback_open):
        super().__init__(tester, test_file, data_files, points, test_extra, feedback_open)

    def check_java(self, test_name, data_file, points_total):
        if data_file is None:
            data_file = 'nodata.sql'
        java_command = ['java', '-cp', self.java_classpath, self.__class__.__name__, self.oracle_database,
                        self.test_database, self.user_name, self.user_password, test_name, data_file, str(points_total)]
        java = subprocess.run(java_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                              check=True)

        return java

    def get_test_results(self, table_name, sql_file, sql_order_file=None):
        query, query_vars = self.select_query(schema_name=self.schema_name, table_name=table_name)
        self.test_cursor.execute(query, query_vars)
        self.test_connection.commit()
        test_results = self.test_cursor.fetchall()

        return test_results

    def run(self):

        # for test_name in sorted(self.specs.keys()):
        #     for data_file, java_points_total in sorted(self.specs[test_name].items()):
        if self.data_file is None:  # connection test
            self.data_name = None
            self.test_data_name = self.test_name
        # JAVA: drop and recreate test schema + dataset, then run java
        java_fail = False
        java_test_data_name = 'JAVA {}'.format(self.test_data_name)
        try:
            self.set_test_schema(self.data_file)
            output = self.check_java(test_name=self.test_name, data_file=self.data_file,
                                     points_total=java_points_total)
            print(output.stdout)
            self.feedback_open.write(output.stderr)
            if '<status>pass</status>' not in output.stdout:
                java_fail = True  # don't run SQL
        except Exception as e:
            self.oracle_connection.commit()
            self.test_connection.commit()
            if isinstance(e, subprocess.CalledProcessError):
                msg = self.ERROR_MSGS['bad_java'].format(e.stdout, e.stderr)
            else:
                msg = str(e)
            self.error(message=msg)
            java_fail = True  # don't run SQL
            # MarkusUtilsMixin.print_test_error(name=java_test_data_name, message=msg,
            #                                   points_total=java_points_total)
            # self.print_file_error(output_open=output_open, name=java_test_data_name, feedback=msg)
        if self.test_name not in self.sql_specs:
            return
        # SQL: fetch and compare sql results
        for table_name, sql_points_total in self.sql_specs[self.test_name][self.data_file]:
            sql_test_data_name = 'SQL({}) {}'.format(table_name, self.test_data_name)
            try:
                if java_fail:
                    raise Exception(self.ERROR_MSGS['skip_sql'])
                test_results = self.get_test_results(table_name=table_name, sql_file=None)
                oracle_results = self.get_oracle_results(schema_name=self.data_name, table_name=table_name)
                message, status = self.check_results(oracle_results=oracle_results, test_results=test_results,
                                                     order_on=False)
                if status == 'pass':
                    return self.passed()
                else:
                    oracle_solution, test_solution = self.get_psql_dump()
                    return self.failed(message, oracle_solution, test_solution)
                # points_awarded = sql_points_total if status == 'pass' else 0
                # MarkusUtilsMixin.print_test_result(name=sql_test_data_name, status=status,
                #                                    output=output, points_awarded=points_awarded,
                #                                    points_total=sql_points_total)
                # self.print_file_psql(output_open=output_open, name=sql_test_data_name,
                #                      oracle_schema_name=data_name, table_name=table_name, status=status,
                #                      feedback=output)
            except Exception as e:
                self.oracle_connection.commit()
                self.test_connection.commit()
                self.error(message=str(e))
                # MarkusUtilsMixin.print_test_error(name=sql_test_data_name, message=str(e),
                #                                   points_total=sql_points_total)
                # self.print_file_error(output_open=output_open, name=sql_test_data_name, feedback=str(e))


class MarkusJDBCTester(MarkusSQLTester):

    CONNECTION_TEST = 'Connection Test'

    def __init__(self, specs, test_class=MarkusJDBCTest):
        super().__init__(specs, test_class)
        self.java_files = specs['java_files']
        self.java_classpath = '.:{}:{}'.format(specs['path_to_solution'], specs['java_jar'])
        self.sql_specs = sql_specs

    def init_java(self):
        javac_command = ['javac', '-cp', self.java_classpath, '{}.java'.format(self.__class__.__name__)]
        subprocess.run(javac_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                       check=True)

    def run(self):
        try:
            for java_file in self.java_files:
                if not os.path.isfile(java_file):
                    msg = MarkusJDBCTest.ERROR_MSGS['no_submission'].format(java_file)
                    print(MarkusTester.error_all(message=msg))
                    return
            try:
                self.init_java()
            except subprocess.CalledProcessError as e:
                msg = MarkusJDBCTest.ERROR_MSGS['bad_javac'].format(e.stdout)
                print(MarkusTester.error_all(message=msg))
                return
        except Exception as e:
            print(MarkusTester.error_all(message=str(e)))
        super().run()
