import edu.toronto.cs.jam.annotations.Description;
import org.junit.Test;

import static org.junit.Assert.assertTrue;

public class Test1 {

    Submission submission = new Submission();

    @Test(timeout=10)
    @Description(description="This test should pass")
    public void testPasses() {
        assertTrue(submission.returnTrue());
    }

    @Test(timeout=10)
    @Description(description="This test should fail")
    public void testFails() {
        assertTrue(submission.returnFalse());
    }

}
