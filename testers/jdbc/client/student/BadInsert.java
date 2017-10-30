import java.sql.PreparedStatement;

public class BadInsert extends Submission {

    public BadInsert() throws ClassNotFoundException {

        super();
    }

    public boolean insert(String newWord) {

        try {
            String sql = "INSERT INTO table1(word) VALUES (?)";
            PreparedStatement statement = this.connection.prepareStatement(sql);
            statement.setString(1, newWord + "X");
            statement.executeUpdate();
            statement.close();

            return true;
        }
        catch (Exception e) {
            return false;
        }
    }

}
