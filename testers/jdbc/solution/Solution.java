import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class Solution {

    Connection connection;

    Solution() throws ClassNotFoundException {

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

    public List<String> select(double numberThreshold) {

        try {
            String sql = "SELECT table1.word FROM table1 JOIN table2 ON table1.id = table2.foreign_id WHERE " +
                         "table2.number > ? ORDER BY word";
            PreparedStatement statement = this.connection.prepareStatement(sql);
            statement.setDouble(1, numberThreshold);
            ResultSet resultSet = statement.executeQuery();
            List<String> result = new ArrayList<>();
            while (resultSet.next()) {
                result.add(resultSet.getString(1));
            }
            statement.close();

            return result;
        }
        catch (Exception e) {
            return null;
        }
    }

    public boolean insert(String newWord) {

        try {
            String sql = "INSERT INTO table1(word) VALUES (?)";
            PreparedStatement statement = this.connection.prepareStatement(sql);
            statement.setString(1, newWord);
            statement.executeUpdate();
            statement.close();

            return true;
        }
        catch (Exception e) {
            return false;
        }
    }

}
