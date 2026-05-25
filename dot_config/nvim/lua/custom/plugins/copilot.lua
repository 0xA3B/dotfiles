return {
  { -- Copilot lua version of github/copilot.vim
    "zbirenbaum/copilot.lua",
    cmd = "Copilot",
    event = "InsertEnter",
    config = function()
      require("copilot").setup({
        panel = {
          -- Set to false when using copilot-cmp-copilot to display suggestions
          enabled = false,
          -- auto_refresh = true,
        },
        suggestion = {
          -- Set to false when using copilot-cmp-copilot to display suggestions
          enabled = false,
          -- auto_trigger = true,
        },
        filetypes = {
          ["*"] = true,
        },
      })
    end,
  },
  { -- Copilot support for blink.cmp
    "giuxtaposition/blink-cmp-copilot",
    config = function()
      require("blink.cmp").add_source_provider("copilot", {
        name = "copilot",
        module = "blink-cmp-copilot",
        score_offset = 100,
        async = true,
      })
    end,
  },
  { -- Copilot Chat
    "CopilotC-Nvim/CopilotChat.nvim",
    dependencies = {
      { "zbirenbaum/copilot.lua" },
      { "nvim-lua/plenary.nvim", branch = "master" }, -- for curl, log and async functions
    },
    build = "make tiktoken", -- Only on MacOS or Linux
    opts = {},
    config = function()
      require("CopilotChat").setup({
        auto_insert_mode = false,
        insert_at_end = true,
        mappings = {
          close = {
            normal = "q",
            insert = "<C-q>",
          },
          submit_prompt = {
            normal = "<C-CR>",
            insert = "<C-CR>",
          },
        },
      })

      vim.keymap.set("n", "<leader>cc", function()
        require("CopilotChat").open({ width = 0.1 })
      end, { desc = "[C]opilot [C]hat" })
    end,
  },
}
