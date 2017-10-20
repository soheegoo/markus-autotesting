import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class Submission {

    Connection connection;

    Submission() throws ClassNotFoundException {

        Class.forName("org.postgresql.Driver");
    }

    public boolean connectDB(String URL, String username, String password) {

        try {
            this.connection = DriverManager.getConnection(URL, username, password);
            return true;
        }
        catch (SQLException e) {
            return false;
        }
    }

    public boolean disconnectDB() {

        try {
            this.connection.close();
            return true;
        }
        catch (SQLException e) {
            return false;
        }
    }

}
