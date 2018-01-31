import org.junit.platform.engine.TestExecutionResult;
import org.junit.platform.engine.discovery.ClassNameFilter;
import org.junit.platform.engine.discovery.DiscoverySelectors;
import org.junit.platform.engine.support.descriptor.MethodSource;
import org.junit.platform.launcher.Launcher;
import org.junit.platform.launcher.LauncherDiscoveryRequest;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestIdentifier;
import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
import org.junit.platform.launcher.core.LauncherFactory;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.Set;

public class MarkusJavaTester {

    public static void main(String[] args) {

        Set<Path> classpath = new HashSet<>();
        classpath.add(Paths.get("."));
        LauncherDiscoveryRequest request = LauncherDiscoveryRequestBuilder.request()
            .selectors(DiscoverySelectors.selectClasspathRoots(classpath))
            .filters(ClassNameFilter.includeClassNamePatterns("Test.*"))
            .build();
        Launcher launcher = LauncherFactory.create();
        launcher.registerTestExecutionListeners(new TestExecutionListener() {
            @Override
            public void executionFinished(TestIdentifier testIdentifier, TestExecutionResult testExecutionResult) {
                if (testIdentifier.isContainer()) {
                    return;
                }
                System.out.println(
                    ((MethodSource) testIdentifier.getSource().get()).getClassName() + "." +
                    testIdentifier.getDisplayName() + ": " +
                    testExecutionResult.getStatus());
                testExecutionResult.getThrowable().ifPresent(t -> System.out.println(t.getMessage()));
            }
        });
        launcher.execute(request);
    }

}
