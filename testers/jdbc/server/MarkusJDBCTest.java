import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;
import java.lang.reflect.Method;
import java.sql.PreparedStatement;
import java.text.MessageFormat;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class MarkusJDBCTest {

    private static class TestResult {
        String msg;
        String status;
        public TestResult(String status, String msg) {
            this.status = status;
            this.msg = msg;
        }
    }

    private static final Map<String, String> ERROR_MSGS = new HashMap<>();
    static {
        ERROR_MSGS.put("bad_connection", "connectDB did not create a valid connection to the database");
        ERROR_MSGS.put("ex_connection", "Connection to the database failed with an exception: ''{0}''");
        ERROR_MSGS.put("bad_disconnection", "disconnectDB did not close the database connection properly");
        ERROR_MSGS.put("ex_disconnection", "Disconnection from the database failed with an exception: ''{0}''");
        ERROR_MSGS.put("bad_output", "Expected the output to be ''{0}'' instead of ''{1}''");
        ERROR_MSGS.put("ex_output", "The test failed with an exception: ''{0}''");
    }
    private static final String CONNECTION_TEST = "Connection Test";

    private String oracleDatabase;
    private String testDatabase;
    private String userName;
    private String userPassword;
    private String dataName;
    private String testName;
    private SubmissionOracle oracle;
    private Submission test;

    public MarkusJDBCTest(String oracleDatabase, String testDatabase, String userName, String userPassword,
                          String dataName, String testName) {

        this.oracleDatabase = oracleDatabase;
        this.testDatabase = testDatabase;
        this.userName = userName;
        this.userPassword = userPassword;
        this.dataName = dataName;
        this.testName = testName;
    }

    private TestResult initDB() {

        try {
            this.oracle = new SubmissionOracle();
            this.test = new Submission();
            final String JDBC_PREAMBLE = "jdbc:postgresql://localhost:5432/";
            boolean testConnected = this.test.connectDB(JDBC_PREAMBLE + this.testDatabase, this.userName,
                                                        this.userPassword);
            if (!testConnected || this.test.connection == null || !this.test.connection.isValid(0)) {
                return new TestResult("fail", ERROR_MSGS.get("bad_connection"));
            }
            this.oracle.connectDB(JDBC_PREAMBLE + this.oracleDatabase, this.userName, this.userPassword);
            if (this.dataName != null) {
                String oracleSchema = "set search_path to " + this.dataName.toLowerCase();
                PreparedStatement ps = this.oracle.connection.prepareStatement(oracleSchema);
                ps.execute();
                ps.close();
            }
            return new TestResult("pass", "");
        }
        catch (Exception e) {
            String msg = MessageFormat.format(ERROR_MSGS.get("ex_connection"), e.getMessage());
            return new TestResult("fail", msg);
        }
    }

    private TestResult closeDB() {

        try {
            boolean testDisconnected = this.test.disconnectDB();
            if (!testDisconnected || (this.test.connection != null && !this.test.connection.isClosed())) {
                try { // try to close manually
                    if (this.test.connection != null) {
                        this.test.connection.close();
                    }
                }
                catch (Exception e) {}
                return new TestResult("fail", ERROR_MSGS.get("bad_disconnection"));
            }
            return new TestResult("pass", "");
        }
        catch (Exception e) {
            String msg = MessageFormat.format(ERROR_MSGS.get("ex_disconnection"), e.getMessage());
            return new TestResult("fail", msg);
        }
        finally {
            try {
                this.oracle.disconnectDB();
            }
            catch (Exception e) {}
        }
    }

    private void run() {

        // redirect stdout and stderr
        PrintStream outOrig = System.out, errOrig = System.err;
        System.setOut(new PrintStream(new OutputStream() {
            public void write(int b) throws IOException {}
        }));
        System.setErr(new PrintStream(new OutputStream() {
            public void write(int b) throws IOException {}
        }));
        // run tests
        TestResult testResult = this.initDB();
        if (testResult.status.equals("pass")) {
            List<Object> inputList = this.oracle.getInputs(this.dataName, this.testName);
            Class[] inputClasses = inputList.stream()
                    .map(Object::getClass)
                    .collect(Collectors.toList())
                    .toArray(new Class[] {});
            Object[] inputs = inputList.toArray(new Object[] {});
            try {
                Method testMethod = this.test.getClass().getMethod(this.testName, inputClasses);
                Object testOutput = testMethod.invoke(this.test, inputs);
                Method oracleMethod = this.oracle.getClass().getMethod(this.testName, inputClasses);
                Object oracleOutput = oracleMethod.invoke(this.oracle, inputs);
                //TODO compare outputs
            } catch (Exception e) {
                //TODO return failure
            }
        }
        TestResult closeResult = this.closeDB();
        if (this.testName.equals(MarkusJDBCTest.CONNECTION_TEST) && testResult.status.equals("pass")) {
            testResult = closeResult;
        }
        // restore stdout and stderr, then print results
        System.setOut(outOrig);
        System.setErr(errOrig);
        System.out.println(testResult.status);
        if (!testResult.status.equals("pass")) {
            System.err.println(testResult.msg);
        }
    }

    public static void main(String args[]) {

        String oracleDatabase = args[0];
        String testDatabase = args[1];
        String userName = args[2];
        String userPassword = args[3];
        String testName = args[4];
        String dataName = args[5];

        MarkusJDBCTest test = new MarkusJDBCTest(oracleDatabase, testDatabase, userName, userPassword, dataName,
                                                 testName);
        test.run();
    }

}
