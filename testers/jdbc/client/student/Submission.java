import java.sql.DriverManager;
import java.sql.SQLException;

public class Submission extends JDBCSubmission {

    Submission() throws ClassNotFoundException {

        Class.forName("org.postgresql.Driver");
    }

    @Override
    public boolean connectDB(String URL, String username, String password) {

        try {
            connection = DriverManager.getConnection(URL, username, password);
            return true;
        }
        catch (SQLException e) {
            return false;
        }
    }

    @Override
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
