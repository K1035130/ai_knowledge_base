<#
Starts the backend EC2 instance and repoints CloudFront's /api/* origin at its new public DNS name
(the instance doesn't have an Elastic IP, so the address changes on every stop/start).
Takes a few minutes: instance boot + status checks, then CloudFront distribution redeploy.
#>

$ErrorActionPreference = "Stop"

$InstanceId = "i-01727c5a8c9173534"
$DistributionId = "E1JY8ZIWY8GN4W"
$Region = "us-east-2"
$ConfigPath = Join-Path $env:TEMP "ai-report-cf-dist-config.json"

Write-Host "Starting EC2 instance $InstanceId..."
aws ec2 start-instances --instance-ids $InstanceId --region $Region | Out-Null

Write-Host "Waiting for instance to reach 'running' state..."
aws ec2 wait instance-running --instance-ids $InstanceId --region $Region

Write-Host "Waiting for instance status checks to pass (this can take a couple minutes)..."
aws ec2 wait instance-status-ok --instance-ids $InstanceId --region $Region

$PublicDns = aws ec2 describe-instances --instance-ids $InstanceId --region $Region --query "Reservations[0].Instances[0].PublicDnsName" --output text
$PublicIp = aws ec2 describe-instances --instance-ids $InstanceId --region $Region --query "Reservations[0].Instances[0].PublicIpAddress" --output text
Write-Host "New public DNS: $PublicDns ($PublicIp)"

Write-Host "Fetching current CloudFront distribution config..."
$current = aws cloudfront get-distribution-config --id $DistributionId --output json --region $Region | ConvertFrom-Json
$etag = $current.ETag
$distConfig = $current.DistributionConfig

$origin = $distConfig.Origins.Items | Where-Object { $_.DomainName -like "ec2-*" } | Select-Object -First 1
if (-not $origin) {
    throw "Could not find the EC2 origin (DomainName starting with 'ec2-') in the CloudFront distribution config."
}

if ($origin.DomainName -eq $PublicDns) {
    Write-Host "CloudFront origin already points at $PublicDns — no update needed."
} else {
    Write-Host "Updating CloudFront origin: $($origin.DomainName) -> $PublicDns"
    $origin.DomainName = $PublicDns

    $distConfig | ConvertTo-Json -Depth 30 | Set-Content -Path $ConfigPath -Encoding utf8

    aws cloudfront update-distribution --id $DistributionId --distribution-config "file://$ConfigPath" --if-match $etag --region $Region | Out-Null
    Remove-Item $ConfigPath -Force

    Write-Host "Waiting for CloudFront distribution to finish deploying (often 5-15 minutes)..."
    aws cloudfront wait distribution-deployed --id $DistributionId --region $Region
}

Write-Host ""
Write-Host "Backend is back up: https://d2lwi9nb2rcmz1.cloudfront.net"
Write-Host "SSH: ssh -i ~/.ssh/ai-report-key.pem ubuntu@$PublicIp"
