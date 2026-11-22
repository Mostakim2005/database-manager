/** Master AI Models Data Catalog (v1.3.1 Dual-Source Verified by update_models.ps1) **/
window.MASTER_CATALOG = [
    {
        "id":  "anthropic/claude-opus-5.5",
        "name":  "Claude Opus 5.5",
        "provider":  "Anthropic",
        "provider_family":  "Anthropic",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 1 (0% to -5%)",
        "frontier_delta_pct":  0,
        "context_window":  "1M",
        "context_tokens":  1000000,
        "scores":  {
                       "intelligence_index":  57.6,
                       "coding_power":  92,
                       "code_arena_elo":  1391,
                       "stem_accuracy_pct":  95
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1000000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  128000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  4,
                        "completion_per_m":  20,
                        "cache_read_per_m":  0.2,
                        "cache_write_per_m":  5,
                        "batch_prompt_per_m":  2,
                        "batch_completion_per_m":  10,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "Tier 1-4 API"
    },
    {
        "id":  "anthropic/claude-sonnet-5.5",
        "name":  "Claude Sonnet 5.5",
        "provider":  "Anthropic",
        "provider_family":  "Anthropic",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 1 (0% to -5%)",
        "frontier_delta_pct":  -2.3,
        "context_window":  "1M",
        "context_tokens":  1000000,
        "scores":  {
                       "intelligence_index":  56,
                       "coding_power":  91,
                       "code_arena_elo":  1365,
                       "stem_accuracy_pct":  92
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1000000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  128000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  2,
                        "completion_per_m":  10,
                        "cache_read_per_m":  0.1,
                        "cache_write_per_m":  2.5,
                        "batch_prompt_per_m":  1,
                        "batch_completion_per_m":  5,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "Claude Pro / API"
    },
    {
        "id":  "anthropic/claude-fable-5.1",
        "name":  "Claude Fable 5.1",
        "provider":  "Anthropic",
        "provider_family":  "Anthropic",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 2 (-5% to -10%)",
        "frontier_delta_pct":  -5.6,
        "context_window":  "1M",
        "context_tokens":  1000000,
        "scores":  {
                       "intelligence_index":  53.4,
                       "coding_power":  90,
                       "code_arena_elo":  1338,
                       "stem_accuracy_pct":  88
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1000000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  128000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  10,
                        "completion_per_m":  50,
                        "cache_read_per_m":  0.25,
                        "cache_write_per_m":  12.5,
                        "batch_prompt_per_m":  5,
                        "batch_completion_per_m":  25,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "Claude API"
    },
    {
        "id":  "google/gemini-4-argon",
        "name":  "Gemini 4 Argon",
        "provider":  "Google",
        "provider_family":  "Google",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 2 (-5% to -10%)",
        "frontier_delta_pct":  -5.4,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  52.6,
                       "coding_power":  86,
                       "code_arena_elo":  1330,
                       "stem_accuracy_pct":  94
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1048576 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  943718
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  2,
                        "completion_per_m":  10,
                        "cache_read_per_m":  0.1,
                        "cache_write_per_m":  0.1875,
                        "batch_prompt_per_m":  1,
                        "batch_completion_per_m":  5,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "Google AI Studio / Browser"
    },
    {
        "id":  "reflection/beam-1.0-501b-a23b",
        "name":  "Beam 1.0 501B A23B",
        "provider":  "Reflection",
        "provider_family":  "Reflection",
        "classification":  "Open-Source",
        "frontier_tier":  "Tier 3 (-10% to -15%)",
        "frontier_delta_pct":  -11,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  49,
                       "coding_power":  83,
                       "code_arena_elo":  1325,
                       "stem_accuracy_pct":  87
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1048576 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  true,
                                                "output_limit":  943718
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0.3,
                        "completion_per_m":  1,
                        "cache_read_per_m":  0.04,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0.15,
                        "batch_completion_per_m":  0.5,
                        "is_free":  false
                    },
        "rate_limits":  "OpenRouter Standard: 200 RPM",
        "quota_and_access":  "OpenRouter / Open Weights"
    },
    {
        "id":  "anthropic/claude-opus-5",
        "name":  "Claude Opus 5",
        "provider":  "Anthropic",
        "provider_family":  "Anthropic",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 2 (-5% to -10%)",
        "frontier_delta_pct":  -8.6,
        "context_window":  "1M",
        "context_tokens":  1000000,
        "scores":  {
                       "intelligence_index":  50.8,
                       "coding_power":  85,
                       "code_arena_elo":  1324,
                       "stem_accuracy_pct":  89
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1000000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  128000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  5,
                        "completion_per_m":  25,
                        "cache_read_per_m":  0.5,
                        "cache_write_per_m":  6.25,
                        "batch_prompt_per_m":  2.5,
                        "batch_completion_per_m":  12.5,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "Claude Pro / API"
    },
    {
        "id":  "openai/gpt-6-astra",
        "name":  "GPT-6 Astra",
        "provider":  "OpenAI",
        "provider_family":  "OpenAI",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 2 (-5% to -10%)",
        "frontier_delta_pct":  -6.4,
        "context_window":  "1M",
        "context_tokens":  1050000,
        "scores":  {
                       "intelligence_index":  52.7,
                       "coding_power":  84,
                       "code_arena_elo":  1320,
                       "stem_accuracy_pct":  93
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1050000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  128000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  10,
                        "completion_per_m":  50,
                        "cache_read_per_m":  1,
                        "cache_write_per_m":  12.5,
                        "batch_prompt_per_m":  5,
                        "batch_completion_per_m":  25,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "ChatGPT Plus / API"
    },
    {
        "id":  "google/gemini-3.5-pro",
        "name":  "Gemini 3.5 Pro",
        "provider":  "Google",
        "provider_family":  "Google",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 3 (-10% to -15%)",
        "frontier_delta_pct":  -11.8,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  46.5,
                       "coding_power":  83,
                       "code_arena_elo":  1318,
                       "stem_accuracy_pct":  89
                   },
        "fact_check":  {
                           "is_verified":  false,
                           "status":  "Verified via OpenRouter",
                           "pricing_concordance":  "Verified Available",
                           "context_concordance":  "Concordant (1M)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  65536
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0,
                        "completion_per_m":  0,
                        "cache_read_per_m":  0,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0,
                        "batch_completion_per_m":  0,
                        "is_free":  false
                    },
        "rate_limits":  "Google AI Studio: 50 RPD",
        "quota_and_access":  "Google AI Studio: 50 RPD"
    },
    {
        "id":  "xiaomi/mimo-v2.6-pro",
        "name":  "Xiaomi MiMo V2.6 Pro",
        "provider":  "Xiaomi",
        "provider_family":  "Xiaomi",
        "classification":  "Open-Source",
        "frontier_tier":  "Tier 3 (-10% to -15%)",
        "frontier_delta_pct":  -14.8,
        "context_window":  "1M",
        "context_tokens":  1050000,
        "scores":  {
                       "intelligence_index":  46.3,
                       "coding_power":  79,
                       "code_arena_elo":  1317,
                       "stem_accuracy_pct":  85
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1050000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  true,
                                                "output_limit":  131072
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  false,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  0.8,
                                                                   "code_delta":  0.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  -2.5,
                                                                    "code_delta":  -1.8,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0.435,
                        "completion_per_m":  0.87,
                        "cache_read_per_m":  0.0036,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0.2175,
                        "batch_completion_per_m":  0.435,
                        "is_free":  false
                    },
        "rate_limits":  "OpenRouter Standard: 200 RPM",
        "quota_and_access":  "Open Code / API"
    },
    {
        "id":  "openai/gpt-6-sol",
        "name":  "GPT-6 Sol",
        "provider":  "OpenAI",
        "provider_family":  "OpenAI",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 3 (-10% to -15%)",
        "frontier_delta_pct":  -11.5,
        "context_window":  "1M",
        "context_tokens":  1050000,
        "scores":  {
                       "intelligence_index":  47.6,
                       "coding_power":  83,
                       "code_arena_elo":  1315,
                       "stem_accuracy_pct":  88
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1050000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  128000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  2,
                        "completion_per_m":  10,
                        "cache_read_per_m":  0.2,
                        "cache_write_per_m":  2.5,
                        "batch_prompt_per_m":  1,
                        "batch_completion_per_m":  5,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "ChatGPT Plus / API"
    },
    {
        "id":  "minimax/MiniMax-M3.1-Flash",
        "name":  "MiniMax-M3.1-Flash",
        "provider":  "MiniMax",
        "provider_family":  "MiniMax",
        "classification":  "Open-Source",
        "frontier_tier":  "Tier 4 (-15% to -20%)",
        "frontier_delta_pct":  -15.5,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  45,
                       "coding_power":  80,
                       "code_arena_elo":  1310,
                       "stem_accuracy_pct":  84
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Verified Available",
                           "context_concordance":  "100% Match (1000000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  false,
                                                "open_weights":  false,
                                                "output_limit":  512000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  false,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  0.8,
                                                                   "code_delta":  0.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  -2.5,
                                                                    "code_delta":  -1.8,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0,
                        "completion_per_m":  0,
                        "cache_read_per_m":  0,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0,
                        "batch_completion_per_m":  0,
                        "is_free":  false
                    },
        "rate_limits":  "OpenRouter Standard: 200 RPM",
        "quota_and_access":  "OpenRouter / Open Weights"
    },
    {
        "id":  "openai/gpt-5.6-sol",
        "name":  "GPT-5.6 Sol",
        "provider":  "OpenAI",
        "provider_family":  "OpenAI",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 3 (-10% to -15%)",
        "frontier_delta_pct":  -12.6,
        "context_window":  "1M",
        "context_tokens":  1050000,
        "scores":  {
                       "intelligence_index":  47,
                       "coding_power":  82,
                       "code_arena_elo":  1308,
                       "stem_accuracy_pct":  87
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1050000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  128000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  4,
                        "completion_per_m":  20,
                        "cache_read_per_m":  0.4,
                        "cache_write_per_m":  5,
                        "batch_prompt_per_m":  2,
                        "batch_completion_per_m":  10,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "ChatGPT Plus / API"
    },
    {
        "id":  "z-ai/glm-5.3",
        "name":  "Z.ai GLM 5.3",
        "provider":  "Z.ai",
        "provider_family":  "Z.ai",
        "classification":  "Open-Source",
        "frontier_tier":  "Tier 4 (-15% to -20%)",
        "frontier_delta_pct":  -16.3,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  44.8,
                       "coding_power":  79,
                       "code_arena_elo":  1306,
                       "stem_accuracy_pct":  83
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1048576 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  true,
                                                "output_limit":  943718
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  false,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  0.8,
                                                                   "code_delta":  0.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  -2.5,
                                                                    "code_delta":  -1.8,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0.079,
                        "completion_per_m":  1.4,
                        "cache_read_per_m":  0.078,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0.0395,
                        "batch_completion_per_m":  0.7,
                        "is_free":  false
                    },
        "rate_limits":  "OpenRouter Standard: 200 RPM",
        "quota_and_access":  "Budget API (.08/M)"
    },
    {
        "id":  "google/gemini-3.8-flash",
        "name":  "Gemini 3.8 Flash",
        "provider":  "Google",
        "provider_family":  "Google",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 4 (-15% to -20%)",
        "frontier_delta_pct":  -18.6,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  40.9,
                       "coding_power":  80,
                       "code_arena_elo":  1305,
                       "stem_accuracy_pct":  82
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1048576 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  65536
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0.825,
                        "completion_per_m":  4.125,
                        "cache_read_per_m":  0.0825,
                        "cache_write_per_m":  0.0417,
                        "batch_prompt_per_m":  0.4125,
                        "batch_completion_per_m":  2.0625,
                        "is_free":  true
                    },
        "rate_limits":  "Free Studio: 1,500 RPD",
        "quota_and_access":  "Free Studio: 1,500 RPD"
    },
    {
        "id":  "openai/gpt-5.6-terra",
        "name":  "GPT-5.6 Terra",
        "provider":  "OpenAI",
        "provider_family":  "OpenAI",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 4 (-15% to -20%)",
        "frontier_delta_pct":  -17.9,
        "context_window":  "1M",
        "context_tokens":  1050000,
        "scores":  {
                       "intelligence_index":  42.1,
                       "coding_power":  81,
                       "code_arena_elo":  1295,
                       "stem_accuracy_pct":  81
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1050000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  128000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  2,
                        "completion_per_m":  12,
                        "cache_read_per_m":  0.2,
                        "cache_write_per_m":  2.5,
                        "batch_prompt_per_m":  1,
                        "batch_completion_per_m":  6,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "ChatGPT Go / API"
    },
    {
        "id":  "qwen/qwen-2.5-coder-32b-instruct",
        "name":  "Qwen 2.5 Coder 32B",
        "provider":  "Alibaba / Qwen",
        "provider_family":  "Alibaba",
        "classification":  "Open-Source",
        "frontier_tier":  "Tier 5 (\u003e -20%)",
        "frontier_delta_pct":  -21.3,
        "context_window":  "33k",
        "context_tokens":  32768,
        "scores":  {
                       "intelligence_index":  39,
                       "coding_power":  78.5,
                       "code_arena_elo":  1292,
                       "stem_accuracy_pct":  79
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (32768 tokens)",
                           "capabilities":  {
                                                "reasoning":  false,
                                                "tool_call":  false,
                                                "structured_output":  false,
                                                "open_weights":  true,
                                                "output_limit":  29491
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  false,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  0.8,
                                                                   "code_delta":  0.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  -2.5,
                                                                    "code_delta":  -1.8,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0.66,
                        "completion_per_m":  1,
                        "cache_read_per_m":  0,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0.33,
                        "batch_completion_per_m":  0.5,
                        "is_free":  false
                    },
        "rate_limits":  "OpenRouter Standard: 200 RPM",
        "quota_and_access":  "Groq / OpenRouter"
    },
    {
        "id":  "google/gemini-3.5-flash",
        "name":  "Gemini 3.5 Flash",
        "provider":  "Google",
        "provider_family":  "Google",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 5 (\u003e -20%)",
        "frontier_delta_pct":  -22,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  38,
                       "coding_power":  77,
                       "code_arena_elo":  1290,
                       "stem_accuracy_pct":  80
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1048576 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  65536
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  1.5,
                        "completion_per_m":  9,
                        "cache_read_per_m":  0.15,
                        "cache_write_per_m":  0.0833,
                        "batch_prompt_per_m":  0.75,
                        "batch_completion_per_m":  4.5,
                        "is_free":  false
                    },
        "rate_limits":  "Google AI Studio: 1,500 RPD",
        "quota_and_access":  "Google AI Studio: 1,500 RPD"
    },
    {
        "id":  "deepseek/deepseek-v4-pro-0813",
        "name":  "DeepSeek V4 Pro (Web)",
        "provider":  "DeepSeek",
        "provider_family":  "DeepSeek",
        "classification":  "Open-Source",
        "frontier_tier":  "Tier 5 (\u003e -20%)",
        "frontier_delta_pct":  -22.1,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  36,
                       "coding_power":  78,
                       "code_arena_elo":  1290,
                       "stem_accuracy_pct":  82
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1048576 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  true,
                                                "output_limit":  384000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  false,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  0.8,
                                                                   "code_delta":  0.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  -2.5,
                                                                    "code_delta":  -1.8,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0.66,
                        "completion_per_m":  1.98,
                        "cache_read_per_m":  0.022,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0.33,
                        "batch_completion_per_m":  0.99,
                        "is_free":  true
                    },
        "rate_limits":  "OpenRouter Standard: 200 RPM",
        "quota_and_access":  "DeepSeek Web Free"
    },
    {
        "id":  "anthropic/claude-opus-4.6",
        "name":  "Claude Opus 4.6",
        "provider":  "Anthropic",
        "provider_family":  "Anthropic",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 5 (\u003e -20%)",
        "frontier_delta_pct":  -31.6,
        "context_window":  "1M",
        "context_tokens":  1000000,
        "scores":  {
                       "intelligence_index":  31.9,
                       "coding_power":  68,
                       "code_arena_elo":  1290,
                       "stem_accuracy_pct":  72
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1000000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  128000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  5,
                        "completion_per_m":  25,
                        "cache_read_per_m":  0.5,
                        "cache_write_per_m":  6.25,
                        "batch_prompt_per_m":  2.5,
                        "batch_completion_per_m":  12.5,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "Claude API"
    },
    {
        "id":  "deepseek/deepseek-v4.1-flash-1017",
        "name":  "DeepSeek 4.1 Flash (1017)",
        "provider":  "DeepSeek",
        "provider_family":  "DeepSeek",
        "classification":  "Free \u0026 Budget",
        "frontier_tier":  "Tier 5 (\u003e -20%)",
        "frontier_delta_pct":  -20.4,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  40.8,
                       "coding_power":  76,
                       "code_arena_elo":  1285,
                       "stem_accuracy_pct":  81
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1048576 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  true,
                                                "output_limit":  393216
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  false,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  0.8,
                                                                   "code_delta":  0.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  -2.5,
                                                                    "code_delta":  -1.8,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0.3,
                        "completion_per_m":  1.2,
                        "cache_read_per_m":  0.006,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0.15,
                        "batch_completion_per_m":  0.6,
                        "is_free":  true
                    },
        "rate_limits":  "OpenRouter Standard: 200 RPM",
        "quota_and_access":  "100% Free in Open Code"
    },
    {
        "id":  "meta/muse-wonder",
        "name":  "Meta Muse Wonder",
        "provider":  "Meta",
        "provider_family":  "Meta",
        "classification":  "Open-Source",
        "frontier_tier":  "Tier 5 (\u003e -20%)",
        "frontier_delta_pct":  -20.8,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  42,
                       "coding_power":  75,
                       "code_arena_elo":  1285,
                       "stem_accuracy_pct":  79
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1048576 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  943718
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  false,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  0.8,
                                                                   "code_delta":  0.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  -2.5,
                                                                    "code_delta":  -1.8,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  4,
                        "completion_per_m":  20,
                        "cache_read_per_m":  0.2,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  2,
                        "batch_completion_per_m":  10,
                        "is_free":  false
                    },
        "rate_limits":  "OpenRouter Standard: 200 RPM",
        "quota_and_access":  "Open Weights"
    },
    {
        "id":  "z-ai/glm-5.3-flash",
        "name":  "GLM 5.3 Flash",
        "provider":  "Z.ai",
        "provider_family":  "Z.ai",
        "classification":  "Free \u0026 Budget",
        "frontier_tier":  "Tier 5 (\u003e -20%)",
        "frontier_delta_pct":  -21.3,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  41.8,
                       "coding_power":  75,
                       "code_arena_elo":  1284,
                       "stem_accuracy_pct":  78
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1048576 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  true,
                                                "output_limit":  943718
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  false,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  0.8,
                                                                   "code_delta":  0.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  -2.5,
                                                                    "code_delta":  -1.8,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0.048,
                        "completion_per_m":  0.16,
                        "cache_read_per_m":  0.006,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0.024,
                        "batch_completion_per_m":  0.08,
                        "is_free":  true
                    },
        "rate_limits":  "OpenRouter Standard: 200 RPM",
        "quota_and_access":  "100% Free in Open Code"
    },
    {
        "id":  "anthropic/claude-sonnet-4.5",
        "name":  "Claude Sonnet 4.5",
        "provider":  "Anthropic",
        "provider_family":  "Anthropic",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 5 (\u003e -20%)",
        "frontier_delta_pct":  -28.7,
        "context_window":  "1M",
        "context_tokens":  1000000,
        "scores":  {
                       "intelligence_index":  34.5,
                       "coding_power":  71,
                       "code_arena_elo":  1282,
                       "stem_accuracy_pct":  73
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1000000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  64000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  3,
                        "completion_per_m":  15,
                        "cache_read_per_m":  0.3,
                        "cache_write_per_m":  3.75,
                        "batch_prompt_per_m":  1.5,
                        "batch_completion_per_m":  7.5,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "Claude API"
    },
    {
        "id":  "meta/muse-spark-1.3",
        "name":  "Meta Muse Spark 1.3",
        "provider":  "Meta",
        "provider_family":  "Meta",
        "classification":  "Open-Source",
        "frontier_tier":  "Tier 3 (-10% to -15%)",
        "frontier_delta_pct":  -13,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  48.1,
                       "coding_power":  82,
                       "code_arena_elo":  1354,
                       "stem_accuracy_pct":  84
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1048576 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  943718
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "Low (Frontier Reasoning Engine)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  1.25,
                        "completion_per_m":  4.25,
                        "cache_read_per_m":  0.15,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0.625,
                        "batch_completion_per_m":  2.125,
                        "is_free":  true
                    },
        "rate_limits":  "OpenRouter Standard: 200 RPM",
        "quota_and_access":  "100% Free in Open Code"
    },
    {
        "id":  "groq/qwen-3.8-27b",
        "name":  "Qwen3.8 27B",
        "provider":  "Alibaba / Groq",
        "provider_family":  "Alibaba",
        "classification":  "Open-Source",
        "frontier_tier":  "Tier 5 (\u003e -20%)",
        "frontier_delta_pct":  -21.1,
        "context_window":  "1M",
        "context_tokens":  1048576,
        "scores":  {
                       "intelligence_index":  40.2,
                       "coding_power":  76,
                       "code_arena_elo":  1280,
                       "stem_accuracy_pct":  80
                   },
        "fact_check":  {
                           "is_verified":  false,
                           "status":  "Verified via OpenRouter",
                           "pricing_concordance":  "100% Free in Open Code",
                           "context_concordance":  "Concordant (1M)",
                           "capabilities":  {
                                                "reasoning":  false,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  true,
                                                "output_limit":  65536
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  false,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  0.8,
                                                                   "code_delta":  0.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  -2.5,
                                                                    "code_delta":  -1.8,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0,
                        "completion_per_m":  0,
                        "cache_read_per_m":  0,
                        "cache_write_per_m":  0,
                        "batch_prompt_per_m":  0,
                        "batch_completion_per_m":  0,
                        "is_free":  true
                    },
        "rate_limits":  "Groq Free: 14.4k RPD",
        "quota_and_access":  "Groq Free: 14.4k RPD"
    },
    {
        "id":  "anthropic/claude-haiku-5.5",
        "name":  "Claude Haiku 5.5",
        "provider":  "Anthropic",
        "provider_family":  "Anthropic",
        "classification":  "Frontier",
        "frontier_tier":  "Tier 4 (-15% to -20%)",
        "frontier_delta_pct":  -19.6,
        "context_window":  "1M",
        "context_tokens":  1000000,
        "scores":  {
                       "intelligence_index":  43.4,
                       "coding_power":  76,
                       "code_arena_elo":  1279,
                       "stem_accuracy_pct":  79
                   },
        "fact_check":  {
                           "is_verified":  true,
                           "status":  "Dual-Source Concordance (OpenRouter + Models.dev)",
                           "pricing_concordance":  "Exact Match (promptPrice / complPrice)",
                           "context_concordance":  "100% Match (1000000 tokens)",
                           "capabilities":  {
                                                "reasoning":  true,
                                                "tool_call":  true,
                                                "structured_output":  true,
                                                "open_weights":  false,
                                                "output_limit":  128000
                                            },
                           "sources":  [
                                           "OpenRouter API",
                                           "Models.dev"
                                       ]
                       },
        "effort_simulation":  {
                                  "supports_effort":  true,
                                  "is_reasoning_core":  true,
                                  "overthinking_risk":  "High (Overthinking Regression Risk on \u003c30B/distilled models)",
                                  "multipliers":  {
                                                      "low":  {
                                                                  "intel_delta":  -1.5,
                                                                  "code_delta":  -1,
                                                                  "token_multiplier":  0.65
                                                              },
                                                      "medium":  {
                                                                     "intel_delta":  0,
                                                                     "code_delta":  0,
                                                                     "token_multiplier":  1
                                                                 },
                                                      "high":  {
                                                                   "intel_delta":  4.5,
                                                                   "code_delta":  3.5,
                                                                   "token_multiplier":  1.6
                                                               },
                                                      "ultra":  {
                                                                    "intel_delta":  7.2,
                                                                    "code_delta":  5.5,
                                                                    "token_multiplier":  2.8
                                                                }
                                                  }
                              },
        "pricing":  {
                        "prompt_per_m":  0.1,
                        "completion_per_m":  0.5,
                        "cache_read_per_m":  0.01,
                        "cache_write_per_m":  0.125,
                        "batch_prompt_per_m":  0.05,
                        "batch_completion_per_m":  0.25,
                        "is_free":  false
                    },
        "rate_limits":  "Tier 1: 50 RPM / 10k RPD",
        "quota_and_access":  "Claude API / Micro-tier"
    }
];
