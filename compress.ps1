$compress = @{
  Path = ".\*.py", ".\requirements.txt"
  CompressionLevel = "Fastest"
  DestinationPath = ".\bot_v5.zip"
}
Compress-Archive @compress