$compress = @{
  Path = ".\*.py", ".\requirements.txt"
  CompressionLevel = "Fastest"
  DestinationPath = ".\bot_v23.zip"
}
Compress-Archive @compress