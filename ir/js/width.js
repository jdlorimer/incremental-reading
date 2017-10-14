if (screen.width > {maxWidth}) {{
    var styleSheet = document.styleSheets[0];
    styleSheet.insertRule(
        "div {{ width: {maxWidth}px; margin: 20px auto }}");
}}
