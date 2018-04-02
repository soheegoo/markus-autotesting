package edu.toronto.cs.teach;

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

import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.Set;

public class MarkusJavaTester {

    private String[] testClasses;

    public MarkusJavaTester(String[] testFiles) {

        this.testClasses = new String[testFiles.length];
        for (int i = 0; i < testFiles.length; i++) {
            testClasses[i] = testFiles[i].split("\\.")[0];
        }
    }

    private void run() {

        // redirect stdout and stderr
        PrintStream outOrig = System.out, errOrig = System.err;
        System.setOut(new PrintStream(new OutputStream() {
            public void write(int b) throws IOException {}
        }));
        System.setErr(new PrintStream(new OutputStream() {
            public void write(int b) throws IOException {}
        }));
        // run tests
        Set<Path> classpath = new HashSet<>();
        classpath.add(Paths.get("."));
        LauncherDiscoveryRequest request = LauncherDiscoveryRequestBuilder.request()
            .selectors(DiscoverySelectors.selectClasspathRoots(classpath))
            .filters(ClassNameFilter.includeClassNamePatterns(this.testClasses))
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
        // restore stdout and stderr, then print results
        System.setOut(outOrig);
        System.setErr(errOrig);
    }

    public static void main(String[] args) {

        MarkusJavaTester tester = new MarkusJavaTester(args);
        tester.run();
    }

}
