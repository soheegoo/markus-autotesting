import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public abstract class JDBCSolution {

    public Connection connection;

    public JDBCSolution() throws ClassNotFoundException {

        Class.forName("org.postgresql.Driver");
    }

    public boolean connectDB(String url, String username, String password) {

        try {
            this.connection = DriverManager.getConnection(url, username, password);
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
