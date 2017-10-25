import java.sql.Connection;

public abstract class JDBCSubmission {

    public Connection connection;

    public abstract boolean connectDB(String url, String username, String password);

    public abstract boolean disconnectDB();

}
