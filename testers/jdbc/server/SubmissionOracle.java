import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class SubmissionOracle {

    Connection connection;

    SubmissionOracle() throws ClassNotFoundException {

        Class.forName("org.postgresql.Driver");
    }

    public boolean connectDB(String URL, String username, String password) {

        try {
            connection = DriverManager.getConnection(URL, username, password);
            return true;
        }
        catch (SQLException e) {
            return false;
        }
    }

    public boolean disconnectDB() {

        try {
            connection.close();
            return true;
        }
        catch (SQLException e) {
            return false;
        }
    }

    /* TODO
     0) Oracle has a main, where it calls inputs = getInputs() and solution.testName(inputs) through reflection
     1) Tester calls inputs = getInputs()
     2) Tester calls test.testName(inputs) through reflection
     3) Tester calls oracle.testName(dataName) through reflection
     4) Tester compares the outputs in a generic way
     */
    public List<Object> getInputs(String dataName, String testName) {

        switch (dataName) {
            case "data1":
            case "data2":
                double number = 0;
                return Arrays.asList(number);
            default:
                return new ArrayList<>();
        }
    }

    public Object selectMethod() {

        return null;
    }

    public Object insertMethod() {

        return null;
    }

}
