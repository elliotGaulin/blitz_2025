$compress = @{
  Path = ".\*.py", ".\requirements.txt"
  CompressionLevel = "Fastest"
  DestinationPath = ".\bot.zip"
}
Compress-Archive @compress