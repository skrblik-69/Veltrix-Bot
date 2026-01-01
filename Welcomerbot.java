import net.dv8tion.jda.api.JDABuilder;
import net.dv8tion.jda.api.events.guild.member.GuildMemberJoinEvent;
import net.dv8tion.jda.api.hooks.ListenerAdapter;
import javax.security.auth.login.LoginException;

public class WelcomeBot extends ListenerAdapter {

    public static void main(String[] args) {
        try {
            JDABuilder builder = JDABuilder.createDefault("YOUR_BOT_TOKEN");
            builder.addEventListeners(new WelcomeBot());
            builder.build();
        } catch (LoginException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onGuildMemberJoin(GuildMemberJoinEvent event) {
        long welcomeChannelID = 1403013049065017355L; // ID kanálu pro uvítání
        event.getGuild().getTextChannelById(welcomeChannelID)
            .sendMessage("Ahoj " + event.getMember().getAsMention() + "! 🎉 Vítej na serveru **" + event.getGuild().getName() + "**.").queue();
    }
}