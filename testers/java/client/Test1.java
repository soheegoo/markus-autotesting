import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

public class Test1 {

    Submission submission = new Submission();

    @Test//(timeout=10000)
    //@Description(description="This test should pass")
    public void testPasses() {
        assertTrue(submission.returnTrue());
    }

    @Test//(timeout=10000)
    //@Description(description="This test should fail")
    public void testFails() {
        assertTrue(submission.returnFalse());
    }

}
