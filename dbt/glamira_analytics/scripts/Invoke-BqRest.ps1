function Invoke-BqRest {
    param(
        [Parameter(Mandatory)]
        [string]$Query,

        [string]$Location = "asia-southeast1"
    )

    $token = gcloud auth print-access-token

    if (-not $token) {
        throw "Unable to obtain Google Cloud access token."
    }

    $headers = @{
        Authorization = "Bearer $token"
    }

    $body = @{
        query        = $Query
        useLegacySql = $false
        location     = $Location
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod `
            -Method POST `
            -Uri "https://bigquery.googleapis.com/bigquery/v2/projects/glamira-pipeline-506706/queries" `
            -Headers $headers `
            -ContentType "application/json" `
            -Body $body `
            -ErrorAction Stop
    }
    catch {
        Write-Error "BigQuery REST request failed: $($_.Exception.Message)"
        return
    }

    if (-not $response.jobComplete) {
        throw "BigQuery job did not complete synchronously."
    }

    if (-not $response.rows) {
        return
    }

    $columns = @(
        $response.schema.fields |
        ForEach-Object { $_.name }
    )

    foreach ($row in $response.rows) {
        $result = [ordered]@{}

        for ($i = 0; $i -lt $columns.Count; $i++) {
            $result[$columns[$i]] = $row.f[$i].v
        }

        [PSCustomObject]$result
    }
}