resource "aws_cloudwatch_log_group" "audit" {
  name              = "/proofgraph/audit"
  retention_in_days = 365
}

resource "aws_cloudtrail" "main" {
  name                          = "proofgraph-trail"
  include_global_service_events = true
}
