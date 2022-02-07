use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct GameBoxScores {
    pub id: String,
    pub home: TeamBoxScore,
    pub away: TeamBoxScore,
}

impl GameBoxScores {
    pub fn try_from_obj(obj: &Map<String, Value>) -> Option<Self> {
        let game = obj.get("game")?.as_object()?;
        let id = game.get("gameId")?.as_str()?;
        let home_team = game.get("homeTeam")?.as_object()?;
        let home = TeamBoxScore::try_from_obj(home_team)?;
        let away_team = game.get("awayTeam")?.as_object()?;
        let away = TeamBoxScore::try_from_obj(away_team)?;

        Some(Self {
            id: id.to_string(),
            home: home,
            away: away,
        })
    }
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct TeamBoxScore {
    pub abv: String,
    pub box_score: BoxScore,
}

impl TeamBoxScore {
    pub fn try_from_obj(obj: &Map<String, Value>) -> Option<Self> {
        let players = obj.get("players")?;
        let box_score = BoxScore::try_from_value(players.clone())?;
        let abv = obj.get("teamTricode")?.as_str()?;
        Some(Self {
            abv: abv.to_string(),
            box_score,
        })
    }
}

#[derive(Debug, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct BoxScore {
    pub assist: Option<TopPlayerByValue>,
    pub blocks: Option<TopPlayerByValue>,
    pub fouled: Option<TopPlayerByValue>,
    pub fouler: Option<TopPlayerByValue>,
    pub steals: Option<TopPlayerByValue>,
    pub turnovers: Option<TopPlayerByValue>,
    pub points: Option<TopPlayerByValue>,
    pub paint_points: Option<TopPlayerByValue>,
    pub threes: Option<TopPlayerByValue>,
    pub rebounds: Option<TopPlayerByValue>,
    pub off_rebounds: Option<TopPlayerByValue>,
    pub def_rebounds: Option<TopPlayerByValue>,
}

impl BoxScore {
    pub fn try_from_value(value: Value) -> Option<Self> {
        let stats: Vec<StatPlayer> = serde_json::from_value(value.clone())
            .map_err(|e| {
                std::fs::write(
                    "box_score_calc_err.json",
                    serde_json::to_string_pretty(&value).unwrap(),
                )
                .unwrap();
                e
            })
            .unwrap();
        let mut ret = BoxScore::default();
        for stat in stats {
            ret.update_assist(stat.player_name.clone(), stat.statistics.assists);
            ret.update_blocks(stat.player_name.clone(), stat.statistics.blocks);
            ret.update_fouled(stat.player_name.clone(), stat.statistics.fouls_drawn);
            ret.update_fouler(stat.player_name.clone(), stat.statistics.fouls_personal);
            ret.update_steals(stat.player_name.clone(), stat.statistics.steals);
            ret.update_turnovers(stat.player_name.clone(), stat.statistics.turnovers);
            ret.update_points(stat.player_name.clone(), stat.statistics.points);
            ret.update_paint_points(
                stat.player_name.clone(),
                stat.statistics.points_in_the_paint,
            );
            ret.update_threes(
                stat.player_name.clone(),
                stat.statistics.three_pointers_made,
            );
            ret.update_rebounds(stat.player_name.clone(), stat.statistics.rebounds_total);
            ret.update_off_rebounds(stat.player_name.clone(), stat.statistics.rebounds_offensive);
            ret.update_def_rebounds(stat.player_name.clone(), stat.statistics.rebounds_defensive);
        }
        Some(ret)
    }

    fn update_assist(&mut self, name: String, value: u8) {
        if let Some(v) = self.assist.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.assist = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_blocks(&mut self, name: String, value: u8) {
        if let Some(v) = self.blocks.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.blocks = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_fouled(&mut self, name: String, value: u8) {
        if let Some(v) = self.fouled.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.fouled = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_fouler(&mut self, name: String, value: u8) {
        if let Some(v) = self.fouler.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.fouler = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_steals(&mut self, name: String, value: u8) {
        if let Some(v) = self.steals.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.steals = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_turnovers(&mut self, name: String, value: u8) {
        if let Some(v) = self.turnovers.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.turnovers = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_points(&mut self, name: String, value: u8) {
        if let Some(v) = self.points.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.points = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_paint_points(&mut self, name: String, value: u8) {
        if let Some(v) = self.paint_points.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.paint_points = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_threes(&mut self, name: String, value: u8) {
        if let Some(v) = self.threes.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.threes = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_rebounds(&mut self, name: String, value: u8) {
        if let Some(v) = self.rebounds.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.rebounds = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_off_rebounds(&mut self, name: String, value: u8) {
        if let Some(v) = self.off_rebounds.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.off_rebounds = Some(TopPlayerByValue { name, value })
        }
    }
    fn update_def_rebounds(&mut self, name: String, value: u8) {
        if let Some(v) = self.def_rebounds.as_mut() {
            if v.value < value {
                *v = TopPlayerByValue { name, value };
            }
        } else {
            self.def_rebounds = Some(TopPlayerByValue { name, value })
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct TopPlayerByValue {
    pub name: String,
    pub value: u8,
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
struct StatPlayer {
    #[serde(alias = "nameI")]
    player_name: String,
    statistics: Stats,
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Stats {
    #[serde(default)]
    pub assists: u8,
    #[serde(default)]
    pub blocks: u8,
    #[serde(default)]
    pub blocks_received: u8,
    #[serde(default)]
    pub field_goals_attempted: u8,
    #[serde(default)]
    pub field_goals_made: u8,
    #[serde(default)]
    pub field_goals_percentage: f32,
    #[serde(default)]
    pub fouls_drawn: u8,
    #[serde(default)]
    pub fouls_offensive: u8,
    #[serde(default)]
    pub fouls_personal: u8,
    #[serde(default)]
    pub fouls_technical: u8,
    #[serde(default)]
    pub free_throws_attempted: u8,
    #[serde(default)]
    pub free_throws_made: u8,
    #[serde(default)]
    pub free_throws_percentage: f32,
    #[serde(default)]
    pub minus: f32,
    #[serde(default)]
    pub minutes: String,
    #[serde(default)]
    pub minutes_calculated: String,
    #[serde(default)]
    pub plus: f32,
    #[serde(default)]
    pub plus_minus_points: f32,
    #[serde(default)]
    pub points: u8,
    #[serde(default)]
    pub points_fast_break: u8,
    #[serde(default)]
    pub points_in_the_paint: u8,
    #[serde(default)]
    pub points_second_chance: u8,
    #[serde(default)]
    pub rebounds_defensive: u8,
    #[serde(default)]
    pub rebounds_offensive: u8,
    #[serde(default)]
    pub rebounds_total: u8,
    #[serde(default)]
    pub steals: u8,
    #[serde(default)]
    pub three_pointers_attempted: u8,
    #[serde(default)]
    pub three_pointers_made: u8,
    #[serde(default)]
    pub three_pointers_percentage: f32,
    #[serde(default)]
    pub turnovers: u8,
    #[serde(default)]
    pub two_pointers_attempted: u8,
    #[serde(default)]
    pub two_pointers_made: u8,
    #[serde(default)]
    pub two_pointers_percentage: f32,
}
