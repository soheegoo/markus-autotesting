import java.sql.Connection;

public abstract class JDBCSubmission {

    Connection connection;

    public abstract boolean connectDB(String URL, String username, String password);

    public abstract boolean disconnectDB();

}
