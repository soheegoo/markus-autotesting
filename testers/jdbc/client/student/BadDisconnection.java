public class BadDisconnection extends Correct {

    public BadDisconnection() throws ClassNotFoundException {

        super();
    }

    @Override
    public boolean disconnectDB() {

        return true;
    }

}
