import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

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

}
