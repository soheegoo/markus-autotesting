public class Test1 {

    Submission submission = new Submission();

    public void testPasses() {
        submission.returnTrue();
    }

    public void testFails() {
        submission.notReturnTrue();
    }

}
