export type EventType =
  // Lifecycle
  | 'AIBorn' | 'AIAged' | 'AIDied' | 'AIReproduced' | 'LifeStageChanged'
  // Needs
  | 'NeedDepleted' | 'NeedSatisfied' | 'NeedCritical'
  // Chemistry
  | 'DopamineReleased' | 'SerotoninChanged' | 'CortisolSpiked'
  | 'OxytocinIncreased' | 'EndorphinReleased' | 'AdrenalineReleased' | 'MelatoninRising'
  // Emotions
  | 'EmotionEmerged' | 'EmotionIntensified' | 'EmotionFaded' | 'MoodShifted'
  // Interactions
  | 'HumanMessageReceived' | 'AIResponded' | 'AIInitiatedContact' | 'MessageIgnored'
  // Memory
  | 'MemoryFormed' | 'MemoryRecalled' | 'MemoryConsolidated' | 'MemoryForgotten' | 'DreamOccurred'
  // Behavioral
  | 'GoalCreated' | 'GoalPursued' | 'GoalAchieved' | 'GoalAbandoned' | 'ActionTaken'
  // Social
  | 'BondFormed' | 'BondStrengthened' | 'BondDamaged' | 'RelationshipEnded'
  // Pain
  | 'PainExperienced' | 'TraumaFormed' | 'Healing'
  // Cognitive
  | 'ThoughtGenerated' | 'InsightFormed' | 'BeliefChanged' | 'PreferenceLearned'
  // System
  | 'TickFast' | 'TickSlow' | 'TickDaily'
  | 'LLMEnabled' | 'LLMDisabled' | 'ModelChanged'
  | 'SystemStarted' | 'SystemStopped'

export interface SentiaEvent {
  id: string
  type: EventType
  payload: Record<string, unknown>
  timestamp: string
  sequence: number
}

export interface SentiaState {
  born_at: string | null
  age_days: number
  life_stage: 'infant' | 'child' | 'adolescent' | 'adult' | 'elder'
  is_alive: boolean
  llm_enabled: boolean
  current_model: string
  needs: Record<string, number>
  chemistry: Record<string, number>
  emotions: Record<string, number>
  dominant_emotion: string
  mood: string
  last_thought: string
  last_thought_at: string | null
  last_interaction_at: string | null
  total_events: number
}

export interface ModelInfo {
  name: string
  size_gb: number
  vram_estimate_gb: number
  fits_in_vram: boolean
  is_installed: boolean
  digest: string
}

export interface WSMessage {
  type: 'event' | 'state_snapshot' | 'pong'
  data?: SentiaEvent
  state?: SentiaState
}
