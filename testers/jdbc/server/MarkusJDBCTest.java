import java.io.*;
import java.lang.reflect.Method;
import java.sql.*;
import java.text.MessageFormat;
import java.util.HashMap;
import java.util.Map;

public class MarkusJDBCTest {

    private static class TestStatus {
        String status;
        String msg;
        public TestStatus(String status, String msg) {
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
    private static final String CONNECTION_TEST = "CONNECTION";
    private static String JDBC_PREAMBLE = "jdbc:postgresql://localhost:5432/";

    private String oracleDatabase;
    private String testDatabase;
    private String userName;
    private String userPassword;
    private String schemaName;
    private String dataName;
    private String className;
    private String methodName;
    private Connection oracleConnection;
    private JDBCSubmission testSubmission;

    public MarkusJDBCTest(String oracleDatabase, String testDatabase, String userName, String userPassword,
                          String schemaName, String dataName, String className, String methodName) {

        this.oracleDatabase = oracleDatabase;
        this.testDatabase = testDatabase;
        this.userName = userName;
        this.userPassword = userPassword;
        this.schemaName = schemaName;
        this.dataName = dataName;
        this.className = className;
        this.methodName = methodName;
    }

    private static Object[] getInputs(String className, String methodName, String dataName) {

        //TODO getInputs should be part of the specs
        switch (className) {
        case "Correct":
        case "BadConnection":
        case "ExceptionConnection":
        case "BadDisconnection":
        case "ExceptionDisconnection":
        case "BadSelect":
        case "ExceptionSelect":
        case "NoInsert":
        case "BadInsert":
        case "ExceptionInsert":
            switch (methodName) {
            case "select":
                switch (dataName) {
                case "data1j":
                case "data2j":
                    double numberThreshold = 0;
                    return new Object[] {numberThreshold};
                default:
                    return null;
                }
            case "insert":
                switch (dataName) {
                case "data1j":
                case "data2j":
                    String newWord = "xxxx";
                    return new Object[] {newWord};
                default:
                    return null;
                }
            default:
                return null;
            }
        default:
            return null;
        }
    }

    private static Object runMethod(Class<?> methodClass, Object methodObject, String methodName, String dataName)
                          throws Exception {

        Object[] inputs = MarkusJDBCTest.getInputs(methodClass.getSimpleName(), methodName, dataName);
        if (inputs == null) {
            throw new Exception("Inputs not found");
        }
        Class[] inputClasses = new Class[inputs.length];
        for (int i = 0; i < inputs.length; i++) {
            inputClasses[i] = inputs[i].getClass();
        }
        Method method = methodClass.getMethod(methodName, inputClasses);

        return method.invoke(methodObject, inputs);
    }

    private static void setSchema(Connection connection, String schemaName) throws SQLException {

        String sql = "SET search_path TO " + schemaName.toLowerCase();
        PreparedStatement statement = connection.prepareStatement(sql);
        statement.execute();
        statement.close();
    }

    private TestStatus initDB() {

        try {
            this.testSubmission = (JDBCSubmission) Class.forName(this.className).newInstance();
            boolean testConnected = this.testSubmission.connectDB(JDBC_PREAMBLE + this.testDatabase, this.userName,
                                                                  this.userPassword);
            if (!testConnected || this.testSubmission.connection == null ||
                                  !this.testSubmission.connection.isValid(0)) {
                return new TestStatus("fail", ERROR_MSGS.get("bad_connection"));
            }
            this.oracleConnection = DriverManager.getConnection(JDBC_PREAMBLE + this.oracleDatabase, this.userName,
                                                                this.userPassword);
            return new TestStatus("pass", "");
        }
        catch (Exception e) {
            String msg = MessageFormat.format(ERROR_MSGS.get("ex_connection"), e.getMessage());
            return new TestStatus("fail", msg);
        }
    }

    private TestStatus closeDB() {

        try {
            boolean testDisconnected = this.testSubmission.disconnectDB();
            if (!testDisconnected || (this.testSubmission.connection != null &&
                                      !this.testSubmission.connection.isClosed())) {
                try { // try to close manually
                    if (this.testSubmission.connection != null) {
                        this.testSubmission.connection.close();
                    }
                }
                catch (Exception e) {}
                return new TestStatus("fail", ERROR_MSGS.get("bad_disconnection"));
            }
            return new TestStatus("pass", "");
        }
        catch (Exception e) {
            String msg = MessageFormat.format(ERROR_MSGS.get("ex_disconnection"), e.getMessage());
            return new TestStatus("fail", msg);
        }
        finally {
            try {
                this.oracleConnection.close();
            }
            catch (Exception e) {}
        }
    }

    private Object getOracleResults() throws Exception {

        String sql = MessageFormat.format("SELECT java_output FROM {0}.{1}_{2}", this.dataName,
                                          this.className.toLowerCase(), this.methodName.toLowerCase());
        PreparedStatement statement = this.oracleConnection.prepareStatement(sql);
        ResultSet resultSet = statement.executeQuery();
        resultSet.next();
        byte[] byteOutput = resultSet.getBytes(1);
        statement.close();
        try (ByteArrayInputStream bis = new ByteArrayInputStream(byteOutput)) {
            try (ObjectInputStream ois = new ObjectInputStream(bis)) {
                return ois.readObject();
            }
        }
    }

    private Object getTestResults() throws Exception {

        MarkusJDBCTest.setSchema(this.testSubmission.connection, this.schemaName);
        return MarkusJDBCTest.runMethod(this.testSubmission.getClass(), this.testSubmission, this.methodName,
                                        this.dataName);
    }

    private TestStatus checkResults(Object oracleResults, Object testResults) {

        if (oracleResults.equals(testResults)) {
            return new TestStatus("pass", "");
        }
        String msg = MessageFormat.format(ERROR_MSGS.get("bad_output"), oracleResults, testResults);
        return new TestStatus("fail", msg);
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
        TestStatus testStatus = this.initDB();
        if (!this.methodName.equals(MarkusJDBCTest.CONNECTION_TEST) && testStatus.status.equals("pass")) {
            try {
                Object testResults = this.getTestResults();
                Object oracleResults = this.getOracleResults();
                testStatus = this.checkResults(oracleResults, testResults);
            }
            catch (Exception e) {
                String msg = MessageFormat.format(ERROR_MSGS.get("ex_output"), e);
                testStatus = new TestStatus("fail", msg);
            }
        }
        TestStatus closeResult = this.closeDB();
        if (this.methodName.equals(MarkusJDBCTest.CONNECTION_TEST) && testStatus.status.equals("pass")) {
            testStatus = closeResult;
        }
        // restore stdout and stderr, then print results
        System.setOut(outOrig);
        System.setErr(errOrig);
        System.out.print(testStatus.status);
        if (!testStatus.status.equals("pass")) {
            System.err.print(testStatus.msg);
        }
    }

    private static void initTestEnv(String oracleDatabase, String userName, String dataName, String className,
                                    String methodName) {

        JDBCSubmission solution = null;
        try {
            String userPassword = new String(System.console().readPassword(
                MessageFormat.format("Password for user {0}: ", userName))); // avoids logging it
            System.out.println(MessageFormat.format("[JDBC-Java] Running method ''{0}.{1}()''", className, methodName));
            solution = (JDBCSubmission) Class.forName(className).newInstance();
            solution.connectDB(JDBC_PREAMBLE + oracleDatabase, userName, userPassword);
            MarkusJDBCTest.setSchema(solution.connection, dataName);
            Object javaOutput = MarkusJDBCTest.runMethod(solution.getClass(), solution, methodName, dataName);
            System.out.println("[JDBC-Java] Storing output into solution table");
            byte[] byteOutput;
            try (ByteArrayOutputStream bos = new ByteArrayOutputStream()) {
                try (ObjectOutputStream oos = new ObjectOutputStream(bos)) {
                    oos.writeObject(javaOutput);
                }
                byteOutput = bos.toByteArray();
            }
            String sql = MessageFormat.format("INSERT INTO {0}_{1}(java_output) VALUES (?)", className.toLowerCase(),
                                              methodName.toLowerCase());
            PreparedStatement statement = solution.connection.prepareStatement(sql);
            statement.setBytes(1, byteOutput);
            statement.executeUpdate();
            statement.close();
        }
        catch (Exception e) {
            System.out.println("[JDBC-Java] Exception:");
            e.printStackTrace();
        }
        finally {
            if (solution != null) {
                solution.disconnectDB();
            }
        }
    }

    public static void main(String args[]) {

        String oracleDatabase = args[0];
        String userName = args[1];
        String userPassword = args[2];
        String schemaName = args[3];
        String testName = args[4];
        String dataName = args[5];
        String testDatabase = (args.length > 6) ? args[6] : null;
        String[] testNames = testName.split("\\.");
        String className = testNames[0];
        String methodName = testNames[1];

        if (testDatabase == null) { // installation
            MarkusJDBCTest.initTestEnv(oracleDatabase, userName, dataName, className, methodName);
        }
        else { // run test
            MarkusJDBCTest test = new MarkusJDBCTest(oracleDatabase, testDatabase, userName, userPassword, schemaName,
                                                     dataName, className, methodName);
            test.run();
        }
    }

}
