import org.w3c.dom.Document;
import org.w3c.dom.Text;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import java.io.StringWriter;

public class MarkusUtils {

    public static class TestResult {

        String msg;
        String status;

        public TestResult(String msg, String status) {

            this.msg = msg;
            this.status = status;
        }
    }

    private static String escapeXml(String unescaped) {

        try {
            Document document = DocumentBuilderFactory.newInstance().newDocumentBuilder().newDocument();
            Text text = document.createTextNode(unescaped);
            Transformer transformer = TransformerFactory.newInstance().newTransformer();
            DOMSource source = new DOMSource(text);
            StringWriter writer = new StringWriter();
            StreamResult result = new StreamResult(writer);
            transformer.setOutputProperty(OutputKeys.OMIT_XML_DECLARATION, "yes");
            transformer.transform(source, result);
            return writer.toString();
        }
        catch (Exception e) {
            return unescaped;
        }
    }

    public static void printTestResult(String name, String status, String output, int pointsAwarded,
                                       Integer pointsTotal) {

        if (pointsTotal != null && pointsTotal <= 0) {
            throw new IllegalArgumentException("The total points must be > 0");
        }
        if (pointsAwarded < 0) {
            throw new IllegalArgumentException("The points awarded must be >= 0");
        }
        if (pointsTotal != null && pointsAwarded > pointsTotal) {
            throw new IllegalArgumentException("The points awarded must be <= the total points");
        }

        String outputEscaped = MarkusUtils.escapeXml(output.replace("\\x00", ""));
        String info = (pointsTotal == null) ? name : "[" + pointsAwarded + "/" + pointsTotal + "] " + name;
        System.err.print(
                "<test>\n" +
                        "<name>" + info + "</name>\n" +
                        "<input></input>\n" +
                        "<expected></expected>\n" +
                        "<actual>" + outputEscaped + "</actual>\n" +
                        "<marks_earned>" + pointsAwarded + "</marks_earned>\n" +
                        "<status>" + status + "</status>\n" +
                        "</test>");
    }

    public static void printTestError(String name, String message, Integer pointsTotal) {

        MarkusUtils.printTestResult(name, "error", message, 0, pointsTotal);
    }

    public static void printFileSummary(String testDataName, String status, String feedback) {

        System.out.print("========== " + testDataName + ": " + status.toUpperCase() + " ==========\n\n");
        if (!feedback.equals("")) {
            System.out.print("## Feedback: " + feedback + "\n\n");
        }
    }

    public static void printFileError(String testDataName, String feedback) {

        MarkusUtils.printFileSummary(testDataName, "error", feedback);
        System.out.print("\n");
    }
}
