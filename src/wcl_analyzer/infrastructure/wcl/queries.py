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

FIGHT_PLAYER_STATS_QUERY = """
query FightPlayerStats($code: String!, $fightIDs: [Int]) {
  reportData {
    report(code: $code) {
      summary: table(dataType: Summary, fightIDs: $fightIDs)
      damage: table(dataType: DamageDone, fightIDs: $fightIDs)
      healing: table(dataType: Healing, fightIDs: $fightIDs)
      deaths: table(dataType: Deaths, fightIDs: $fightIDs)
    }
  }
}
"""
