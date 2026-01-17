$compress = @{
  Path = ".\*.py", ".\requirements.txt"
  CompressionLevel = "Fastest"
  DestinationPath = ".\bot_v14.zip"
}
Compress-Archive @compress