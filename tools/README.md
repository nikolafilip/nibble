# tools

`freerouting-2.1.0.jar` is not in git (64 MB). Download it from
https://github.com/freerouting/freerouting/releases/tag/v2.1.0 and run it
headless with Java 21:

    java -Djava.awt.headless=true -jar tools/freerouting-2.1.0.jar -de board.dsn -do board.ses -mp 50

Newer releases need Java 25.
