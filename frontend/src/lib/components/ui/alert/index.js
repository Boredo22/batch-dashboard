import { tv } from "tailwind-variants";
import Alert from "./Alert.svelte";
import AlertDescription from "./AlertDescription.svelte";
import AlertTitle from "./AlertTitle.svelte";

export const alertVariants = tv({
	base: "alert",
	variants: {
		variant: {
			default: "alert-default",
			destructive: "alert-destructive",
			success: "alert-success",
			warning: "alert-warning", 
			info: "alert-info",
			purple: "alert-purple",
			green: "alert-green"
		}
	},
	defaultVariants: {
		variant: "default"
	}
});

export { Alert, AlertDescription, AlertTitle };