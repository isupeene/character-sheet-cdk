package ca.isupeene.charactersheet.cdk;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.google.protobuf.MessageLite;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/**
 * Identifiers for the resource types that plugins can support.
 * Supporting ICON and INFO types is required if any content in your pack
 * specifies an ImageSource or an InfoSource. The other types are optional,
 * depending on what kind of custom content you want to add. The {@link #Tag tag}
 * associated with each DlcType is the String that is provided as the first argument
 * of your ContentProvider's {@link ContentProviderBase#call} function when that
 * type of content is requested.
 *
 * For types other than INFO and ICON, the associated parse function is provided for convenience.
 *
 * EXCEPTION is also included to specify the Bundle key that's used to pass an error back to the app.
 */
public enum DlcType {
    /**
     * "backgrounds" - Indicates that the requested / returned value is a {@link Model.BackgroundList BackgroundList}
     */
    BACKGROUND("backgrounds", Parser::ParseBackgroundList),
    /**
     * "class_spells" - Indicates that the requested / returned value is a {@link Model.ClassSpellsList ClassSpellsList}
     */
    CLASS_SPELLS("class_spells", Parser::ParseClassSpellsList),
    /**
     * "classes" - Indicates that the requested / returned value is a {@link Model.ClassList ClassList}
     */
    CLASS("classes", Parser::ParseClassList),
    /**
     * "feats" - Indicates that the requested / returned value is a {@link Model.FeatList FeatList}
     */
    FEAT("feats", Parser::ParseFeatList),
    /**
     * "items" - Indicates that the requested / returned value is a {@link Model.ItemList ItemList}
     */
    ITEM("items", Parser::ParseItemList),
    /**
     * "races" - Indicates that the requested / returned value is a {@link Model.RaceList RaceList}
     */
    RACE("races", Parser::ParseRaceList),
    /**
     * "races" - Indicates that the requested / returned value is a {@link Model.SpellList SpellList}
     */
    SPELL("spells", Parser::ParseSpellList),
    /**
     * "talents" - Indicates that the requested / returned value is a {@link Model.TalentList TalentList}
     */
    TALENT("talents", Parser::ParseTalentList),
    /**
     * "info" - Indicates that the requested / returned value is a {@link Model.MultiPageInfo MultiPageInfo}
     */
    INFO("info", null),
    /**
     * "image" - Indicates that the requested / returned value is a {@link android.graphics.Bitmap Bitmap}
     */
    IMAGE("image", null),
    /**
     * "exception" - Indicates that the returned value is an error message String.
     */
    EXCEPTION("exception", null);

    private final String tag;
    /**
     * @return
     * The String tag associated with this DlcType.
     */
    public String Tag() { return tag; }

    private final FunctionX<InputStream, MessageLite.Builder, IOException> parser;
    /**
     * @return
     * The parser associated with this DlcType, or null for INFO, IMAGE, and EXCEPTION.
     */
    public FunctionX<InputStream, MessageLite.Builder, IOException> Parser() { return parser; }

    DlcType(@NonNull String tag, @Nullable FunctionX<InputStream, MessageLite.Builder, IOException> parser) {
        this.tag = tag;
        this.parser = parser;
    }

    private static final Map<String, DlcType> typesByTag = new HashMap<>();

    /**
     * @param tag
     * A String identifying a particular DlcType.
     * @return
     * The DlcType associated with the provided tag. This is the DlcType for which the {@link #Tag Tag} function returns the specified tag.
     * @throws EnumConstantNotPresentException
     * If the provided tag does not refer to any DlcType.
     */
    public static DlcType ForTag(@NonNull String tag) throws EnumConstantNotPresentException {
        DlcType result = typesByTag.get(tag);
        if (result == null) throw new EnumConstantNotPresentException(DlcType.class, tag);
        return result;
    }

    static {
        for (DlcType type : values()) {
            typesByTag.put(type.tag, type);
        }
    }
}
