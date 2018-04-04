import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.fail;

public class Test2 {

    Submission submission = new Submission();

    //@Test//(timeout=10000)
    //@Description(description="This test should timeout")
    //public void testLoops() {
    //    submission.loop();
    //}

    @Test//(timeout=10000)
    //@Description(description="This test should fail and print xml")
    public void testFailsAndOutputsXml() {
        fail(submission.returnXml());
    }

}
