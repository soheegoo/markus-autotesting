import edu.toronto.cs.jam.annotations.Description;
import org.junit.Test;

import static org.junit.Assert.fail;

public class Test2 {

    Submission submission = new Submission();

    @Test(timeout=10)
    @Description(description="This test should timeout")
    public void testLoops() {
        submission.loop();
    }

    @Test(timeout=10)
    @Description(description="This test should fail and print xml")
    public void testFailsAndOutputsXml() {
        fail(submission.returnXml());
    }

}
