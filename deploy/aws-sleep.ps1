<#
Stops the backend EC2 instance to pause compute billing.
CloudFront/S3 keep serving the static frontend; /api/* becomes unreachable until aws-wake.ps1 runs.
#>

$ErrorActionPreference = "Stop"

$InstanceId = "i-01727c5a8c9173534"
$Region = "us-east-2"

Write-Host "Stopping EC2 instance $InstanceId..."
aws ec2 stop-instances --instance-ids $InstanceId --region $Region | Out-Null

Write-Host "Waiting for instance to reach 'stopped' state..."
aws ec2 wait instance-stopped --instance-ids $InstanceId --region $Region

Write-Host 'Instance stopped. Compute + public IP billing stopped; only the EBS volume is still billed (~$1-2/month).'
Write-Host "The frontend (S3/CloudFront) stays up, but /api/* calls will fail until you run deploy\aws-wake.ps1."
