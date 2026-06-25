/**
 * Plan Mode Extension
 *
 * A toggleable planning/discussion mode for Pi. When enabled, file system
 * mutations are restricted to docs/PLAN.md and terminal execution is disabled.
 *
 * Keyboard shortcut:
 *   Ctrl + P  → Toggle Plan Mode ON/OFF
 *
 * Restrictions when Plan Mode is ON:
 *   - Allowed file write/edit target: docs/PLAN.md (relative to project root)
 *   - Blocked: writes/edits to any other file
 *   - Blocked: creation of files outside docs/PLAN.md
 *   - Blocked: terminal/bash execution
 *   - Blocked: file deletion (no dedicated delete tool exists; bash is blocked,
 *     preventing rm/mv/delete operations)
 *
 * When Plan Mode is OFF:
 *   - All tools behave normally.
 */

import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import path from "node:path";

const ALLOWED_PLAN_FILE = "docs/plan.md";
const STATE_KEY = "plan-mode-state";

export default function planModeExtension(pi: ExtensionAPI): void {
	// In-memory state per session. Restored from session entries on startup.
	let planModeEnabled = false;

	/**
	 * Normalize a filesystem path so we can compare it against ALLOWED_PLAN_FILE.
	 * Converts Windows backslashes to forward slashes and removes leading "./" or
	 * absolute prefixes that point to the current working directory.
	 */
	function normalizePath(inputPath: string, cwd: string): string {
		let normalized = inputPath.replace(/\\/g, "/").toLowerCase();
		const cwdPrefix = cwd.replace(/\\/g, "/").toLowerCase();
		if (normalized.startsWith(cwdPrefix + "/")) {
			normalized = normalized.slice(cwdPrefix.length + 1);
		}
		normalized = normalized.replace(/^\.\//, "");
		return normalized;
	}

	/**
	 * Return true if the given path is the allowed planning document.
	 */
	function isAllowedPlanFile(inputPath: string, cwd: string): boolean {
		return normalizePath(inputPath, cwd) === ALLOWED_PLAN_FILE;
	}

	/**
	 * Toggle Plan Mode on or off and notify the user.
	 */
	function togglePlanMode(ctx: ExtensionContext): void {
		planModeEnabled = !planModeEnabled;
		persistState();

		if (planModeEnabled) {
			ctx.ui.notify("Plan Mode: ON", "info");
		} else {
			ctx.ui.notify("Plan Mode: OFF", "info");
		}
	}

	/**
	 * Persist Plan Mode state in the session so it survives restarts.
	 */
	function persistState(): void {
		pi.appendEntry(STATE_KEY, { enabled: planModeEnabled });
	}

	/**
	 * Restore Plan Mode state from a previous session if present.
	 */
	function restoreState(ctx: ExtensionContext): void {
		const entries = ctx.sessionManager.getEntries();
		const stateEntry = entries
			.filter(
				(e: { type: string; customType?: string }) =>
					e.type === "custom" && e.customType === STATE_KEY,
			)
			.pop() as { data?: { enabled: boolean } } | undefined;

		if (stateEntry?.data) {
			planModeEnabled = stateEntry.data.enabled ?? false;
		}
	}

	// Register the /plan command as an alternative way to toggle.
	pi.registerCommand("plan", {
		description: "Toggle Plan Mode",
		handler: async (_args, ctx) => {
			togglePlanMode(ctx);
		},
	});

	// Register Ctrl+P keyboard shortcut to toggle Plan Mode.
	// Note: If Pi already binds Ctrl+P to another feature, this handler will run
	// alongside or replace it depending on extension load order.
	pi.registerShortcut("ctrl+p", {
		description: "Toggle Plan Mode",
		handler: async (ctx) => {
			togglePlanMode(ctx);
		},
	});

	// Restore state at startup and update UI accordingly.
	pi.on("session_start", async (_event, ctx) => {
		restoreState(ctx);
		if (planModeEnabled) {
			ctx.ui.setStatus("plan-mode", "Plan Mode: ON");
		} else {
			ctx.ui.setStatus("plan-mode", undefined);
		}
	});

	// Intercept tool calls to enforce Plan Mode restrictions.
	pi.on("tool_call", async (event, ctx) => {
		if (!planModeEnabled) return;

		const cwd = ctx.cwd;

		// Block all terminal execution while Plan Mode is enabled.
		if (event.toolName === "bash") {
			return {
				block: true,
				reason: "Plan Mode is enabled. Terminal execution is disabled.",
			};
		}

		// Block file writes/edits unless they target docs/PLAN.md.
		if (event.toolName === "write" || event.toolName === "edit") {
			const targetPath = (event.input.path as string) ?? "";
			if (!isAllowedPlanFile(targetPath, cwd)) {
				return {
					block: true,
					reason: `Plan Mode is enabled. Only "${ALLOWED_PLAN_FILE}" may be written or modified.`,
				};
			}
		}

		// Continue normally for read and any other allowed tools.
	});

	// Inject a clear planning instruction into the system context when Plan Mode is active.
	pi.on("before_agent_start", async () => {
		if (!planModeEnabled) return;

		return {
			message: {
				customType: "plan-mode-context",
				content: `[PLAN MODE ACTIVE]
You are in Plan Mode. This is a discussion/planning-only session.

Restrictions:
- You may read files normally.
- You may ONLY write or modify: docs/PLAN.md
- You may NOT write, edit, create, delete, or rename any other file.
- You may NOT run terminal commands or execute any bash commands.

When the user asks for a plan, write it to docs/PLAN.md. Otherwise discuss the plan without making file changes.`,
				display: false,
			},
		};
	});
}
