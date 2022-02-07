use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, PartialEq)]
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

impl Action {
    pub fn number(&self) -> i64 {
        match self {
            Action::Period(info) => info.number,
            Action::JumpBall(info) => info.number,
            Action::Points(info) => info.number,
            Action::Rebound(info) => info.number,
            Action::Stoppage(info) => info.number,
            Action::Block(info) => info.number,
            Action::Turnover(info) => info.number,
            Action::Steal(info) => info.number,
            Action::Timeout(info) => info.number,
            Action::Substitution(info) => info.number,
            Action::Foul(info) => info.number,
            Action::FreeThrow(info) => info.number,
            Action::Violation(info) => info.number,
            Action::Game(info) => info.number,
            Action::Unknown(info) => info.number,
        }
    }

    pub fn quarter(&self) -> u8 {
        match self {
            Action::Period(info) => info.quarter,
            Action::JumpBall(info) => info.quarter,
            Action::Points(info) => info.quarter,
            Action::Rebound(info) => info.quarter,
            Action::Stoppage(info) => info.quarter,
            Action::Block(info) => info.quarter,
            Action::Turnover(info) => info.quarter,
            Action::Steal(info) => info.quarter,
            Action::Timeout(info) => info.quarter,
            Action::Substitution(info) => info.quarter,
            Action::Foul(info) => info.quarter,
            Action::FreeThrow(info) => info.quarter,
            Action::Violation(info) => info.quarter,
            Action::Game(info) => info.quarter,
            Action::Unknown(info) => info.quarter,
        }
    }

    pub fn desc(&self) -> &str {
        match self {
            Action::Period(info) => &info.desc,
            Action::JumpBall(info) => &info.desc,
            Action::Points(info) => &info.desc,
            Action::Rebound(info) => &info.desc,
            Action::Stoppage(info) => &info.desc,
            Action::Block(info) => &info.desc,
            Action::Turnover(info) => &info.desc,
            Action::Steal(info) => &info.desc,
            Action::Timeout(info) => &info.desc,
            Action::Substitution(info) => &info.desc,
            Action::Foul(info) => &info.desc,
            Action::FreeThrow(info) => &info.desc,
            Action::Violation(info) => &info.desc,
            Action::Game(info) => &info.desc,
            Action::Unknown(info) => &info.desc,
        }
    }

    pub fn clock(&self) -> &str {
        match self {
            Action::Period(info) => &info.clock,
            Action::JumpBall(info) => &info.clock,
            Action::Points(info) => &info.clock,
            Action::Rebound(info) => &info.clock,
            Action::Stoppage(info) => &info.clock,
            Action::Block(info) => &info.clock,
            Action::Turnover(info) => &info.clock,
            Action::Steal(info) => &info.clock,
            Action::Timeout(info) => &info.clock,
            Action::Substitution(info) => &info.clock,
            Action::Foul(info) => &info.clock,
            Action::FreeThrow(info) => &info.clock,
            Action::Violation(info) => &info.clock,
            Action::Game(info) => &info.clock,
            Action::Unknown(info) => &info.clock,
        }
    }
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub struct ActionInfo {
    #[serde(alias = "actionNumber")]
    number: i64,
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
        let number = value.get("actionNumber")?.as_i64()?;
        let ty = value.get("actionType")?.as_str()?;
        let quarter = value.get("period")?.as_u64()?;
        let clock = duration_to_clock(value.get("clock")?.as_str()?)?;
        let home_score: u16 = value.get("scoreHome")?.as_str()?.parse().ok()?;
        let away_score: u16 = value.get("scoreAway")?.as_str()?.parse().ok()?;
        let mut inner = ActionInfo {
            number,
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
                let what = value.get("shotResult")?.as_str()?;
                inner.desc = format!("{} 2pts {} {} {}", what, team, player, sub.to_lowercase());
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

pub fn duration_to_clock(d: &str) -> Option<String> {
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
