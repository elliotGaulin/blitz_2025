$compress = @{
  Path = ".\*.py", ".\requirements.txt"
  CompressionLevel = "Fastest"
  DestinationPath = ".\bot_v18.zip"
}
Compress-Archive @compress