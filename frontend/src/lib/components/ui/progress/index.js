import { tv } from "tailwind-variants";
import Progress from "./Progress.svelte";

export const progressVariants = tv({
	base: "progress-root",
	variants: {
		variant: {
			default: "",
			destructive: "progress-destructive",
			success: "progress-success", 
			warning: "progress-warning",
			purple: "progress-purple",
			green: "progress-green"
		},
		size: {
			default: "",
			sm: "progress-sm",
			lg: "progress-lg"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});

export { Progress };