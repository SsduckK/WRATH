"""GraphQL documents used by the Warcraft Logs infrastructure."""

REPORT_WITH_FIGHTS_QUERY = """
query ReportWithFights($code: String!) {
  reportData {
    report(code: $code) {
      code
      title
      fights {
        id
        name
        startTime
        endTime
        friendlyPlayers
      }
      masterData {
        actors(type: "Player") {
          id
          name
          type
          subType
        }
      }
    }
  }
  rateLimitData {
    limitPerHour
    pointsSpentThisHour
    pointsResetIn
  }
}
"""
