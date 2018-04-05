import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;
import static org.junit.jupiter.api.Assertions.fail;

public class Test2 {

    Submission submission = new Submission();

    @Test
    @DisplayName("This test should timeout")
    public void testLoops() {
        assertTimeoutPreemptively(Duration.ofSeconds(10), () -> {
            submission.loop();
        });
    }

    @Test
    @DisplayName("This test should fail and print xml")
    public void testFailsAndOutputsXml() {
        fail(submission.returnXml());
    }

}
