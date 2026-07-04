"""Raw GraphQL query strings for LeetCode's public, unauthenticated API.

Kept as plain module-level constants rather than a template engine -- these
never take more than one or two variables and readability wins over
abstraction here.
"""

PROFILE_AND_STATS_QUERY = """
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
      realName
      userAvatar
      countryName
    }
    submitStats: submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
      totalSubmissionNum {
        difficulty
        count
      }
    }
  }
}
"""

CONTEST_RANKING_QUERY = """
query userContestRankingInfo($username: String!) {
  userContestRanking(username: $username) {
    attendedContestsCount
    rating
    globalRanking
    topPercentage
  }
}
"""

DAILY_CHALLENGE_QUERY = """
query questionOfToday {
  activeDailyCodingChallengeQuestion {
    date
    link
    question {
      title
      titleSlug
      difficulty
      acRate
    }
  }
}
"""

USER_CALENDAR_QUERY = """
query userProfileCalendar($username: String!, $year: Int) {
  matchedUser(username: $username) {
    userCalendar(year: $year) {
      streak
      totalActiveDays
      submissionCalendar
    }
  }
}
"""
