
use serde::{Deserialize, Serialize};


#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum Action {
    Period(ActionInfo),
    JumpBall(ActionInfo),
    Points(ActionInfo),
    Rebound(ActionInfo),
    Stoppage(ActionInfo),
    Block(ActionInfo),
    Turnover(ActionInfo),
    Steal(ActionInfo),
    Timeout(ActionInfo),
    Substitution(ActionInfo),
    Foul(ActionInfo),
    FreeThrow(ActionInfo),
    Violation(ActionInfo),
    Game(ActionInfo),
    Unknown(ActionInfo),
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ActionInfo {
    clock: String,
    desc: String,
    home_score: u16,
    away_score: u16,
    quarter: u8,
}

impl Action {
    pub fn try_from_obj(
        value: serde_json::Map<String, serde_json::Value>,
        home_team: &str,
        away_team: &str,
    ) -> Option<Self> {
        let ty = value.get("actionType")?.as_str()?;
        let quarter = value.get("period")?.as_u64()?;
        let clock = duration_to_clock(value.get("clock")?.as_str()?)?;
        let home_score: u16 = value.get("scoreHome")?.as_str()?.parse().ok()?;
        let away_score: u16 = value.get("scoreAway")?.as_str()?.parse().ok()?;
        let mut inner = ActionInfo {
            quarter: quarter as u8,
            clock: clock.to_string(),
            home_score,
            away_score,
            desc: String::new(),
        };
        let ret = match ty {
            "period" => {
                let sub = value.get("subType")?.as_str()?.to_string();
                inner.desc = format!("Q{} {}", inner.quarter, sub);
                Self::Period(inner)
            }
            "jumpball" => {
                inner.desc = value.get("description")?.as_str()?.to_string();
                if inner.desc.is_empty() {
                    inner.desc = format!("Jump won by {}", value.get("teamTricode")?.as_str()?);
                }
                Self::JumpBall(inner)
            }
            "2pt" => {
                let team = value.get("teamTricode")?.as_str()?;
                let player = value.get("playerNameI")?.as_str()?;
                let sub = value.get("subType")?.as_str()?;
                inner.desc = format!("2pts {} {} {}", team, player, sub);
                Self::Points(inner)
            }
            "3pt" => {
                let team = value.get("teamTricode")?.as_str()?;
                let player = value.get("playerNameI")?.as_str()?;
                let sub = value.get("subType")?.as_str()?;
                inner.desc = format!("3pts {} {} {}", team, player, sub);
                Self::Points(inner)
            }
            "rebound" => {
                let team = value.get("teamTricode")?.as_str()?;
                let player = value.get("playerNameI")?.as_str()?;
                let sub = value.get("subType")?.as_str()?;
                inner.desc = format!("{} rebound {} ({})", sub, player, team);
                Self::Rebound(inner)
            }
            "block" => {
                let player = value.get("playerNameI")?.as_str()?;
                inner.desc = format!("Block {}", player);
                Self::Block(inner)
            }
            "turnover" => {
                let from = value.get("teamTricode")?.as_str()?;
                let to = if from == home_team {
                    away_team
                } else {
                    home_team
                };
                inner.desc = format!("Turnover {} -> {}", from, to);
                Self::Turnover(inner)
            }
            "steal" => {
                let from = value.get("teamTricode")?.as_str()?;
                let to = if from == home_team {
                    away_team
                } else {
                    home_team
                };
                inner.desc = format!("Steal {} -> {}", from, to);
                Self::Steal(inner)
            }
            "timeout" => {
                let team = value.get("teamTricode")?.as_str()?;
                inner.desc = format!("Timout {}", team);
                Self::Timeout(inner)
            }
            "substitution" => {
                let who = value.get("playerNameI")?.as_str()?;
                let direction = value.get("subType")?.as_str()?;
                inner.desc = format!("Sub {} {}", who, direction);
                Self::Substitution(inner)
            }
            "foul" => {
                let to = value.get("playerNameI")?.as_str()?;
                let from = value.get("foulDrawnPlayerName")?.as_str()?;
                let from_total = value.get("foulPersonalTotal")?.as_str()?;
                inner.desc = format!("Foul {} <- {} ({})", to, from, from_total);
                Self::Foul(inner)
            }
            "freethrow" => {
                let who = value.get("playerNameI")?.as_str()?;
                let which = value.get("subType")?.as_str()?;
                let result = value.get("shotResult")?.as_str()?;
                inner.desc = format!("Free Throw {} {} {}", who, which, result);
                Self::FreeThrow(inner)
            }
            "violation" => {
                let team = value.get("teamTricode")?.as_str()?;
                let what = value.get("subType")?.as_str()?;
                inner.desc = format!("{} {}", team, what);
                Self::Violation(inner)
            }
            _ => return None,
        };
        Some(ret)
    }
}

fn duration_to_clock(d: &str) -> Option<String> {
    let mut chars = d.chars();
    let p = chars.next()?;
    if p != 'P' {
        return None;
    }
    let t = chars.next()?;
    if t != 'T' {
        return None;
    }
    let mut ret = String::new();
    for ch in chars {
        if ch == 'M' {
            ret.push(':');
            continue;
        }
        if ch == '.' {
            break;
        }
        ret.push(ch)
    }
    Some(ret)
}
