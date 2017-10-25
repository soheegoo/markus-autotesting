import java.io.*;
import java.lang.reflect.Method;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.text.MessageFormat;
import java.util.HashMap;
import java.util.Map;

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
    private static final String CONNECTION_TEST = "CONNECTION";
    private static String JDBC_PREAMBLE = "jdbc:postgresql://localhost:5432/";

    private String oracleDatabase;
    private String testDatabase;
    private String userName;
    private String userPassword;
    private String dataName;
    private String className;
    private String methodName;
    private Connection oracleConnection;
    private JDBCSubmission testSubmission;

    public MarkusJDBCTest(String oracleDatabase, String testDatabase, String userName, String userPassword,
                          String dataName, String className, String methodName) {

        this.oracleDatabase = oracleDatabase;
        this.testDatabase = testDatabase;
        this.userName = userName;
        this.userPassword = userPassword;
        this.dataName = dataName;
        this.className = className;
        this.methodName = methodName;
    }

    private static Object[] getInputs(String className, String methodName, String dataName) {

        //TODO getInputs should be part of the specs
        switch (className) {
        case "Correct":
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

        String oracleSchema = "SET search_path TO " + schemaName.toLowerCase();
        PreparedStatement ps = connection.prepareStatement(oracleSchema);
        ps.execute();
        ps.close();
    }

    private TestResult initDB() {

        try {
            this.testSubmission = (JDBCSubmission) Class.forName(this.className).newInstance();
            boolean testConnected = this.testSubmission.connectDB(JDBC_PREAMBLE + this.testDatabase, this.userName,
                                                                  this.userPassword);
            if (!testConnected || this.testSubmission.connection == null ||
                                  !this.testSubmission.connection.isValid(0)) {
                return new TestResult("fail", ERROR_MSGS.get("bad_connection"));
            }
            //TODO handle our failure differently from student's?
            this.oracleConnection = DriverManager.getConnection(JDBC_PREAMBLE + this.oracleDatabase, this.userName,
                                                                this.userPassword);
            if (this.dataName != null) {
                MarkusJDBCTest.setSchema(this.oracleConnection, this.dataName);
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
            boolean testDisconnected = this.testSubmission.disconnectDB();
            if (!testDisconnected || (this.testSubmission.connection != null &&
                                      !this.testSubmission.connection.isClosed())) {
                try { // try to close manually
                    if (this.testSubmission.connection != null) {
                        this.testSubmission.connection.close();
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
                this.oracleConnection.close();
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
            try {
                //TODO do I need the schema to set it for students?
                Object testOutput = MarkusJDBCTest.runMethod(this.testSubmission.getClass(), this.testSubmission,
                                                             this.methodName, this.dataName);
                //TODO read solution table and deserialize the object
                byte[] byteOutput = null;
                Object oracleOutput = null;
                try (ByteArrayInputStream bis = new ByteArrayInputStream(byteOutput)) {
                    try (ObjectInputStream ois = new ObjectInputStream(bis)) {
                        oracleOutput = ois.readObject();
                    }
                }
                if (oracleOutput.equals(testOutput)) {
                    //TODO compare outputs
                }
            }
            catch (Exception e) {
                //TODO return failure
            }
        }
        TestResult closeResult = this.closeDB();
        if (this.methodName.equals(MarkusJDBCTest.CONNECTION_TEST) && testResult.status.equals("pass")) {
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

    private static void initTestEnv(String oracleDatabase, String userName, String dataName, String className,
                                    String methodName) {

        JDBCSolution solution = null;
        try {
            String userPassword = new String(System.console().readPassword(
                MessageFormat.format("Password for user {0}: ", userName))); // avoids logging it
            System.out.println(MessageFormat.format("[JDBC-Java] Running method ''{0}.{1}()''", className, methodName));
            solution = (JDBCSolution) Class.forName(className).newInstance();
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
                                              methodName);
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
        String testName = args[3];
        String dataName = args[4];
        String testDatabase = (args.length > 5) ? args[5] : null;
        String[] testNames = testName.split("\\.");
        String className = testNames[0];
        String methodName = testNames[1];

        if (testDatabase == null) { // installation
            MarkusJDBCTest.initTestEnv(oracleDatabase, userName, dataName, className, methodName);
        }
        else { // run test
            MarkusJDBCTest test = new MarkusJDBCTest(oracleDatabase, testDatabase, userName, userPassword, dataName,
                                                     className, methodName);
            test.run();
        }
    }

}
